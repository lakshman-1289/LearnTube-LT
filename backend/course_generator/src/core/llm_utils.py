import re
import json
from typing import Any


def clean_llm_json(response: str) -> Any:
    """
    Clean and parse LLM responses that may be wrapped in Markdown, code fences, or extra text.

    Steps:
    1. If response is empty -> raise ValueError
    2. Try json.loads(response) directly
    3. Remove triple-backtick fences (```json ... ``` or ``` ... ```)
    4. Extract the first balanced JSON object or array using brace/bracket counting
    5. json.loads on the extracted substring
    6. If all fails, raise ValueError with a short excerpt of the raw response

    Returns parsed Python object (dict or list).
    """
    if not response or not response.strip():
        raise ValueError("Empty response from LLM")

    preview = response[:200].replace('\n', ' ')
    print(f"[LLM_PARSE] Raw response preview: {preview}")

    # 1) direct parse attempt
    try:
        parsed = json.loads(response)
        print(f"[LLM_PARSE] Direct json.loads succeeded")
        return parsed
    except Exception:
        pass

    # 2) remove triple-backtick code fences (```json ... ``` or ``` ... ```)
    # capture inner content
    fence_pattern = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
    m = fence_pattern.search(response)
    if m:
        candidate = m.group(1).strip()
        try:
            parsed = json.loads(candidate)
            print(f"[LLM_PARSE] Parsed JSON from code fence")
            print(f"[LLM_PARSE] Cleaned JSON preview: {str(candidate)[:200]}")
            return parsed
        except Exception:
            # fall through to bracket extraction
            response = candidate

    # 3) attempt to extract first balanced {...} or [...] substring
    def _extract_balanced(s: str):
        # find first opening brace or bracket
        for i, ch in enumerate(s):
            if ch in '{[':
                start = i
                stack = [ch]
                pairs = {'{': '}', '[': ']'}
                for j in range(i+1, len(s)):
                    c = s[j]
                    if c in '{[':
                        stack.append(c)
                    elif c in '}]':
                        if not stack:
                            break
                        last = stack.pop()
                        if pairs.get(last) != c:
                            # mismatch; give up on this start
                            break
                        if not stack:
                            return s[start:j+1]
                # if we finish loop without closing, continue searching later
        return None

    candidate = _extract_balanced(response)
    if candidate:
        try:
            parsed = json.loads(candidate)
            print(f"[LLM_PARSE] Extracted and parsed balanced JSON")
            print(f"[LLM_PARSE] Cleaned JSON preview: {candidate[:200]}")
            return parsed
        except Exception:
            # try a relaxed regex extraction of {...}
            pass

    # 4) fallback: regex find the largest {...} block
    regex_obj = re.compile(r"\{(?:[^{}]*|(?R))*\}", re.DOTALL)
    m2 = regex_obj.search(response)
    if m2:
        candidate = m2.group(0)
        try:
            parsed = json.loads(candidate)
            print(f"[LLM_PARSE] Parsed JSON from regex fallback")
            return parsed
        except Exception:
            pass

    # final failure
    raise ValueError(f"Unable to extract JSON from LLM response. Raw preview: {preview}")


def normalize_lesson_json(data: dict) -> dict:
    """
    Ensure the lesson JSON matches the expected LessonContent schema:

    {
      "lessonTitle": "string",
      "introduction": "string",
      "sections": [ {"heading": "string", "content": "string"} ],
      "conclusion": "string"
    }

    This function will:
    - Convert common variants (title, lesson_title, lessonSubtitle -> lessonTitle)
    - Fill missing string fields with empty strings
    - Normalize sections into a list of {heading, content} dicts
    - Log (via print) which fields were missing or auto-corrected

    Returns the normalized dict.
    """
    if not isinstance(data, dict):
        print("[LLM_NORMALIZE] Input is not an object; coercing to dict")
        # If LLM returned a list of sections, wrap into lesson structure
        if isinstance(data, list):
            data = {"lessonTitle": "", "introduction": "", "sections": data, "conclusion": ""}
        else:
            data = {}

    corrections = {}

    def _get_first(*keys, default=""):
        for k in keys:
            if k in data and data[k] is not None:
                return data[k]
        return default

    lesson_title = _get_first("lessonTitle", "lesson_title", "title", "name")
    if lesson_title == "":
        corrections["lessonTitle"] = ""

    introduction = _get_first("introduction", "intro", "summary", "lessonSubtitle")
    if introduction == "":
        corrections.setdefault("introduction", "")

    raw_sections = _get_first("sections", "parts", "content", "body", [])

    # Normalize sections into a list of {heading, content}
    normalized_sections = []
    if isinstance(raw_sections, dict):
        # maybe mapping heading->content
        for k, v in raw_sections.items():
            normalized_sections.append({"heading": str(k), "content": str(v)})
    elif isinstance(raw_sections, list):
        for item in raw_sections:
            if isinstance(item, dict):
                heading = item.get("heading") or item.get("title") or item.get("name") or ""
                content = item.get("content") or item.get("text") or item.get("body") or ""
                normalized_sections.append({"heading": str(heading), "content": str(content)})
            elif isinstance(item, str):
                # plain string becomes a single section
                normalized_sections.append({"heading": "", "content": str(item)})
            else:
                # unknown item -> stringify
                normalized_sections.append({"heading": "", "content": str(item)})
    else:
        # Not a list/dict -> coerce to single section
        if raw_sections:
            normalized_sections.append({"heading": "", "content": str(raw_sections)})

    if not normalized_sections:
        corrections.setdefault("sections", [])

    conclusion = _get_first("conclusion", "outro", "closing", "summary_end")
    if conclusion == "":
        corrections.setdefault("conclusion", "")

    normalized = {
        "lessonTitle": str(lesson_title) if lesson_title is not None else "",
        "introduction": str(introduction) if introduction is not None else "",
        "sections": normalized_sections,
        "conclusion": str(conclusion) if conclusion is not None else "",
    }

    # Log corrections
    if corrections:
        print(f"[LLM_NORMALIZE] Auto-filled or normalized fields: {list(corrections.keys())}")
        print(f"[LLM_NORMALIZE] Normalized JSON preview: {str(normalized)[:300]}")

    return normalized


def normalize_sections(sections) -> list:
    """
    Normalize a sections value into a list of {title, type, points} dictionaries.
    Ensures type is strictly 'concept' or 'example'.
    Ensures points is strictly a list of {subtitle, content} dicts.
    """
    result = []
    if not sections:
        return []

    # mapping case
    if isinstance(sections, dict):
        sections = [{"title": str(k), "content": str(v)} for k, v in sections.items()]
    elif not isinstance(sections, list):
        sections = [{"title": "", "content": str(sections)}]

    for sec in sections:
        if not isinstance(sec, dict):
            sec = {"title": "", "content": str(sec)}

        # FIX type
        sec_type = sec.get("type", "").lower()
        if sec_type not in ["concept", "example"]:
            sec_type = "concept"

        title = sec.get("title") or sec.get("heading") or sec.get("name") or ""

        # FIX points
        raw_points = sec.get("points")
        if raw_points is None:
            raw_points = sec.get("content") or sec.get("text") or sec.get("body") or ""

        if not isinstance(raw_points, list):
            if raw_points:
                raw_points = [raw_points]
            else:
                raw_points = []

        fixed_points = []
        for p in raw_points:
            if isinstance(p, str):
                fixed_points.append({"subtitle": "Detail", "content": p})
            elif isinstance(p, dict):
                sub = p.get("subtitle") or p.get("title") or "Detail"
                cnt = p.get("content") or p.get("text") or str(p)
                fixed_points.append({"subtitle": str(sub), "content": str(cnt)})
            else:
                fixed_points.append({"subtitle": "Detail", "content": str(p)})

        result.append({
            "title": str(title),
            "type": sec_type,
            "points": fixed_points
        })

    return result


def normalize_lesson(data: dict) -> dict:
    """
    Coerce any LLM output into the canonical LessonContent shape:

    {
      "lessonTitle": str,
      "introduction": str,
      "sections": [ {"title": str, "type": str, "points": [str,...]} ],
      "conclusion": str
    }

    Logs original vs normalized keys and returns the normalized dict.
    """
    orig_preview = None
    try:
        orig_preview = str(data)[:400]
    except Exception:
        orig_preview = "<unprintable>"

    if not isinstance(data, dict):
        print("[LLM_NORMALIZE] normalize_lesson: input was not an object; coercing")
        data = {}

    lesson_title = data.get("lessonTitle") or data.get("lesson_title") or data.get("title") or data.get("name") or ""
    introduction = data.get("introduction") or data.get("intro") or data.get("summary") or data.get("lessonSubtitle") or ""
    raw_sections = data.get("sections") or data.get("parts") or data.get("content") or data.get("body") or []
    conclusion = data.get("conclusion") or data.get("outro") or data.get("closing") or data.get("summary_end") or ""

    sections = normalize_sections(raw_sections)

    normalized = {
        "lessonTitle": str(lesson_title) if lesson_title is not None else "",
        "introduction": str(introduction) if introduction is not None else "",
        "sections": sections,
        "conclusion": str(conclusion) if conclusion is not None else "",
    }

    # Log differences
    print(f"[LLM_NORMALIZE] Original preview: {orig_preview}")
    print(f"[LLM_NORMALIZE] Normalized preview: {str(normalized)[:400]}")

    # Detect and log missing fields
    missing = [k for k, v in normalized.items() if (v == "" or v == [] and k != "sections")]
    if missing:
        print(f"[LLM_NORMALIZE] Missing or empty fields auto-filled: {missing}")

    return normalized
