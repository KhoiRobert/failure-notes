"""LLM-based root cause detection from scenario context using LangChain."""

import logging
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from app.config import settings
from app.schemas.root_cause import RootCauseCreate

logger = logging.getLogger(__name__)


class DetectRootCauseResult(BaseModel):
    """Result of detect_root_cause_from_context: use existing id or create new with create_data."""

    existing_id: Optional[int] = Field(default=None, description="ID of existing root cause to use")
    create_data: Optional[RootCauseCreate] = Field(default=None, description="Data to create a new root cause")


class RootCauseMatchResult(BaseModel):
    """Structured output: which existing root cause ID matches the context, or 0 if none."""

    root_cause_id: int = Field(description="ID of the matching root cause, or 0 if no match")


class DetectedRootCause(BaseModel):
    """Structured output from LLM for root cause detection."""

    title: str = Field(description="Short root cause title (e.g. 'Timeout under load')")
    description: Optional[str] = Field(
        default=None,
        description="Brief explanation of why this is the root cause",
    )
    solution: Optional[str] = Field(
        default=None,
        description="Abstract, general recommended fix or mitigation for this type of root cause (not specific to any scenario)",
    )


def _find_matching_root_cause(context: str, root_causes: List[Any]) -> Optional[int]:
    """Ask LLM whether any existing root cause matches the scenario context. Returns id or None."""
    if not root_causes or not (getattr(settings, "AI_API_KEY", None) or "").strip():
        return None
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        import json
        import re
    except ImportError:
        return None
    try:
        lines = []
        for rc in root_causes:
            if isinstance(rc, dict):
                rid = rc.get("id")
                title = (rc.get("title") or "") or ""
            else:
                rid = getattr(rc, "id", None)
                title = (getattr(rc, "title", None) or "") or ""
            if rid and title:
                lines.append(f"- ID {rid}: {title}")
        root_causes_text = "\n".join(lines) if lines else "(no root causes)"
        llm = ChatOpenAI(
            model=settings.AI_MODEL,
            api_key=settings.AI_API_KEY,
            base_url=settings.AI_API_URL.rstrip("/") if settings.AI_API_URL else None,
            temperature=0.0,
        )
        
        # Try structured output first
        try:
            structured_llm = llm.with_structured_output(RootCauseMatchResult)
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are an expert at matching failure scenarios to root causes based on their titles. "
                        "Given a scenario context and a list of existing root cause titles (with IDs), "
                        "return the ID of the root cause whose title best matches the scenario's underlying problem.\n\n"
                        "CRITICAL MATCHING RULES:\n"
                        "1. Match based on the UNDERLYING ROOT CAUSE described by the title, not exact wording\n"
                        "2. Scenarios describing the same type of problem should match the same root cause title\n"
                        "3. Minor word differences in the scenario (like 'this' vs 'that') should NOT prevent matching\n"
                        "4. Focus on semantic meaning: if the scenario describes the same failure pattern as a root cause title, they match\n"
                        "5. Be lenient: when in doubt, match to an existing root cause rather than creating a new one\n"
                        "6. The root cause title represents the core problem type - match scenarios to titles that describe the same problem type\n\n"
                        "Return root_cause_id=0 ONLY if the scenario describes a fundamentally different type of problem "
                        "that doesn't match any existing root cause title.",
                    ),
                    ("human", "Scenario context:\n\n{context}\n\nExisting root cause titles:\n{root_causes}\n\n"
                        "Which root cause ID matches this scenario? (Return 0 if none match)"),
                ]
            )
            chain = prompt | structured_llm
            result: RootCauseMatchResult = chain.invoke(
                {"context": context or "(empty)", "root_causes": root_causes_text}
            )
            if result and result.root_cause_id and result.root_cause_id > 0:
                return result.root_cause_id
            return None
        except Exception as structured_error:
            # Fallback to JSON parsing if structured output fails
            error_str = str(structured_error).lower()
            if "tool_use_failed" in error_str or "did not call a tool" in error_str:
                logger.debug("Structured output not supported for matching, falling back to JSON parsing")
                prompt = ChatPromptTemplate.from_messages(
                    [
                        (
                            "system",
                            "You are an expert at matching failure scenarios to root causes. "
                            "Given a scenario context and a list of existing root cause titles (with IDs), "
                            "return the ID of the root cause whose title best matches the scenario's underlying problem.\n\n"
                            "Return ONLY a JSON object with 'root_cause_id' field. Return 0 if no match.\n"
                            'Format: {"root_cause_id": 123}',
                        ),
                        ("human", "Scenario context:\n\n{context}\n\nExisting root cause titles:\n{root_causes}\n\n"
                            "Which root cause ID matches this scenario? (Return 0 if none match)"),
                    ]
                )
                chain = prompt | llm
                response = chain.invoke(
                    {"context": context or "(empty)", "root_causes": root_causes_text}
                )
                
                # Extract JSON from response
                content = response.content if hasattr(response, "content") else str(response)
                json_match = re.search(r'\{[^{}]*"root_cause_id"[^{}]*\}', content)
                if json_match:
                    data = json.loads(json_match.group(0))
                    root_cause_id = data.get("root_cause_id", 0)
                    if root_cause_id and root_cause_id > 0:
                        return root_cause_id
            else:
                # Re-raise if it's not a structured output error
                raise structured_error
        
        return None
        
    except Exception as e:
        err_str = str(e).lower()
        if "429" in err_str or "insufficient_quota" in err_str:
            logger.warning(
                "Root cause match failed (quota/billing): %s. See https://platform.openai.com/account/billing",
                e,
            )
        else:
            logger.warning("Root cause match failed: %s", e, exc_info=True)
        return None


def _create_new_root_cause_from_context(context: str) -> Optional[RootCauseCreate]:
    """Use LLM to infer root cause (title, description, abstract solution). Returns None on failure."""
    if not (getattr(settings, "AI_API_KEY", None) or "").strip():
        return None
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        import json
        import re
    except ImportError:
        logger.warning("LangChain not installed; skipping root cause detection")
        return None
    
    try:
        llm = ChatOpenAI(
            model=settings.AI_MODEL,
            api_key=settings.AI_API_KEY,
            base_url=settings.AI_API_URL.rstrip("/") if settings.AI_API_URL else None,
            temperature=0.2,
        )
        
        # Try structured output first (works with OpenAI models)
        try:
            structured_llm = llm.with_structured_output(DetectedRootCause)
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are an expert at analyzing failure scenarios and identifying root causes. "
                        "Given a user's failure scenario context, output a concise root cause: title, optional description, "
                        "and solution. The solution must be an abstract, general recommendation for this type of root cause "
                        "(e.g. how to fix or prevent it in general), not specific to this single scenario.",
                    ),
                    ("human", "Failure scenario context:\n\n{context}"),
                ]
            )
            chain = prompt | structured_llm
            result: DetectedRootCause = chain.invoke({"context": context or "(empty)"})
            if result and (result.title or "").strip():
                return RootCauseCreate(
                    title=(result.title or "").strip(),
                    description=(result.description or "").strip() or None,
                    solution=(result.solution or "").strip() or None,
                )
        except Exception as structured_error:
            # Fallback to JSON parsing if structured output fails
            error_str = str(structured_error).lower()
            if "tool_use_failed" in error_str or "did not call a tool" in error_str:
                logger.debug("Structured output not supported, falling back to JSON parsing")
                # Use regular LLM call with JSON format instruction
                prompt = ChatPromptTemplate.from_messages(
                    [
                        (
                            "system",
                            "You are an expert at analyzing failure scenarios and identifying root causes. "
                            "Given a user's failure scenario context, output a JSON object with: title (required), "
                            "description (optional), and solution (optional). The solution must be an abstract, general "
                            "recommendation for this type of root cause, not specific to this single scenario.\n\n"
                            "Respond ONLY with valid JSON in this format:\n"
                            '{"title": "Root Cause Title", "description": "Optional description", "solution": "Optional solution"}',
                        ),
                        ("human", "Failure scenario context:\n\n{context}"),
                    ]
                )
                chain = prompt | llm
                response = chain.invoke({"context": context or "(empty)"})
                
                # Extract JSON from response
                content = response.content if hasattr(response, "content") else str(response)
                
                # Try to find JSON in the response
                json_match = re.search(r'\{[^{}]*"title"[^{}]*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    data = json.loads(json_str)
                    if data.get("title"):
                        return RootCauseCreate(
                            title=data.get("title", "").strip(),
                            description=data.get("description", "").strip() or None,
                            solution=data.get("solution", "").strip() or None,
                        )
                
                logger.warning("Could not parse JSON from LLM response: %s", content[:200])
            else:
                # Re-raise if it's not a structured output error
                raise structured_error
        
        return None
        
    except Exception as e:
        err_str = str(e).lower()
        if "429" in err_str or "insufficient_quota" in err_str:
            logger.warning(
                "Root cause detection failed (quota/billing): %s. "
                "Add payment at https://platform.openai.com/account/billing or check usage at https://platform.openai.com/account/usage",
                e,
            )
        else:
            logger.warning("Root cause detection failed: %s", e, exc_info=True)
        return None


def detect_root_cause_from_context(
    context: str,
    existing_root_causes: Optional[List[Any]] = None,
) -> DetectRootCauseResult:
    """
    1. Check if scenario context matches any existing root cause (by title/description). If yes, use it.
    2. Else create a new root cause from context via LLM and return create_data.
    Returns DetectRootCauseResult with existing_id set or create_data set, or both None if LLM unavailable.
    """
    context = (context or "").strip()
    if not context:
        return DetectRootCauseResult(existing_id=None, create_data=None)
    if not (getattr(settings, "AI_API_KEY", None) or "").strip():
        return DetectRootCauseResult(existing_id=None, create_data=None)

    # Step 1: Match context to existing root cause
    if existing_root_causes:
        matched_id = _find_matching_root_cause(context, existing_root_causes)
        if matched_id is not None:
            return DetectRootCauseResult(existing_id=matched_id, create_data=None)

    # Step 2: No match — create new root cause from context (with abstract solution)
    create_data = _create_new_root_cause_from_context(context)
    if create_data:
        return DetectRootCauseResult(existing_id=None, create_data=create_data)
    logger.warning("No root cause created: LLM returned no data (see previous log for reason, e.g. quota or API key)")
    return DetectRootCauseResult(existing_id=None, create_data=None)
