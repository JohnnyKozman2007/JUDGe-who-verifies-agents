import re
import unicodedata
from typing import Dict, List, Optional, TypedDict


SCIENCE_FINAL_ANSWER_FORMAT = "FINAL ANSWER: <A, B, C, or D>"
VALID_OPTION_LABELS = ("A", "B", "C", "D")


class ParsedScienceAnswer(TypedDict):
    letter: Optional[str]
    option_text: Optional[str]
    mode: Optional[str]
    confidence: str
    ambiguous: bool
    notes: List[str]


def normalize_option_text(text: str) -> str:
    """Normalize option/candidate text for robust matching without destroying scientific notation."""
    if text is None:
        return ""

    text = unicodedata.normalize("NFKC", str(text))
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.strip().lower()
    text = re.sub(r"[“”]", '"', text)
    text = re.sub(r"[‘’]", "'", text)
    text = re.sub(r"[‐‑‒–—−]", "-", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\"'`*_]+", "", text)
    text = re.sub(r"\s*[\.,;:!?]+\s*$", "", text)
    return text.strip()


def render_science_question(question_stem: str, options: List[str]) -> str:
    """Render GPQA-style options in a stable A-D format."""
    lines = [str(question_stem).strip(), "Options:"]
    for idx, option_text in enumerate(options):
        label = chr(65 + idx)
        lines.append(f"{label}. {str(option_text).strip()}")
    return "\n".join(lines) + "\n"


def build_option_map(options: List[str]) -> Dict[str, str]:
    return {chr(65 + idx): str(option).strip() for idx, option in enumerate(options)}


def validate_science_options(options: List[str]) -> List[str]:
    issues = []

    if len(options) != 4:
        issues.append(f"expected 4 options, found {len(options)}")
        return issues

    normalized = [normalize_option_text(option) for option in options]

    for idx, option in enumerate(normalized):
        if not option:
            issues.append(f"option {chr(65 + idx)} is empty")

    seen: Dict[str, str] = {}
    for idx, option in enumerate(normalized):
        label = chr(65 + idx)
        if option in seen:
            issues.append(f"option {label} duplicates option {seen[option]}")
        else:
            seen[option] = label

    return issues


def validate_option_map(option_map: Dict[str, str]) -> List[str]:
    issues = []

    labels = set(option_map.keys())
    expected = set(VALID_OPTION_LABELS)

    if labels != expected:
        issues.append(f"option_map labels are {sorted(labels)}, expected {sorted(expected)}")

    ordered_options = [option_map.get(label, "") for label in VALID_OPTION_LABELS]
    issues.extend(validate_science_options(ordered_options))

    return issues


def extract_option_map_from_question(question_text: str) -> Dict[str, str]:
    """
    Extract A-D options from rendered question text, including multiline options.

    This handles cases like:
    A. 1. Zn, ether
       2. HCl
       3. Aq. KOH
    B. ...
    """
    if not question_text:
        return {}

    text = question_text.replace("\r\n", "\n").replace("\r", "\n")
    pattern = re.compile(
        r"(?ms)^\s*([A-D])\.\s*(.*?)(?=^\s*[A-D]\.\s|\Z)"
    )

    option_map: Dict[str, str] = {}
    for match in pattern.finditer(text):
        label = match.group(1).upper()
        body = match.group(2).strip()
        if label in VALID_OPTION_LABELS:
            option_map[label] = body

    return option_map


def _new_parse_result() -> ParsedScienceAnswer:
    return {
        "letter": None,
        "option_text": None,
        "mode": None,
        "confidence": "none",
        "ambiguous": False,
        "notes": [],
    }


def _set_letter(
    parsed: ParsedScienceAnswer,
    letter: str,
    mode: str,
    confidence: str,
    option_map: Optional[Dict[str, str]],
) -> ParsedScienceAnswer:
    letter = letter.upper()
    parsed["letter"] = letter
    parsed["mode"] = mode
    parsed["confidence"] = confidence

    if option_map and letter in option_map:
        parsed["option_text"] = option_map[letter]

    return parsed


def _unique_preserving_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def parse_science_candidate_answer(
    candidate_text: Optional[str],
    option_map: Optional[Dict[str, str]] = None,
) -> ParsedScienceAnswer:
    """
    Extract the selected A-D option from a model's science answer.

    Priority:
    1. Strict final-answer line.
    2. Explicit final/correct answer statements.
    3. Last-line standalone letter if the last line is just an answer.
    4. Unique option-text match.
    5. Conservative tail fallback, marked low confidence.
    """
    parsed = _new_parse_result()

    if not candidate_text:
        parsed["notes"].append("empty_candidate_text")
        return parsed

    text = unicodedata.normalize("NFKC", str(candidate_text))
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()

    if not text:
        parsed["notes"].append("blank_candidate_text")
        return parsed

    option_map = option_map or {}

    if option_map:
        issues = validate_option_map(option_map)
        if issues:
            parsed["notes"].extend([f"option_map_issue:{issue}" for issue in issues])

    # 1. Strict final-answer line. This is the safest and should dominate.
    strict_final = re.findall(
        r"(?im)^\s*FINAL\s+ANSWER\s*[:\-]\s*\(?\s*([A-D])\s*\)?\s*(?:[\.!]?\s*)$",
        text,
    )
    strict_final = _unique_preserving_order([x.upper() for x in strict_final])

    if len(strict_final) == 1:
        return _set_letter(parsed, strict_final[0], "strict_final_answer", "high", option_map)
    if len(strict_final) > 1:
        parsed["ambiguous"] = True
        parsed["notes"].append(f"multiple_strict_final_answers:{','.join(strict_final)}")
        return parsed

    # 2. Explicit answer statements. Prefer later statements because models often conclude at the end.
    explicit_patterns = [
        r"(?i)\b(?:the\s+)?final\s+answer\s*(?:is|:|-)?\s*\(?\s*([A-D])\s*\)?",
        r"(?i)\b(?:the\s+)?correct\s+(?:answer|option)\s*(?:is|:|-)?\s*\(?\s*([A-D])\s*\)?",
        r"(?i)\b(?:answer|option)\s*(?:is|:|-)\s*\(?\s*([A-D])\s*\)?",
        r"(?i)\bI\s+(?:choose|select)\s*(?:option\s*)?\(?\s*([A-D])\s*\)?",
        r"(?i)\bTherefore[, ]+(?:the\s+)?(?:answer|option)\s*(?:is|:|-)?\s*\(?\s*([A-D])\s*\)?",
    ]

    explicit_matches: List[str] = []
    for pattern in explicit_patterns:
        explicit_matches.extend([m.upper() for m in re.findall(pattern, text)])

    explicit_unique = _unique_preserving_order(explicit_matches)
    if explicit_matches:
        last_explicit = explicit_matches[-1]
        if len(set(explicit_matches[-3:])) == 1:
            return _set_letter(parsed, last_explicit, "explicit_answer_statement", "high", option_map)

        parsed["notes"].append(f"conflicting_explicit_answers:{','.join(explicit_unique)}")
        parsed["ambiguous"] = True
        return _set_letter(parsed, last_explicit, "explicit_answer_statement_conflicting", "medium", option_map)

    # 3. Last-line answer-only fallback.
    nonempty_lines = [line.strip() for line in text.split("\n") if line.strip()]
    if nonempty_lines:
        last_line = nonempty_lines[-1]
        last_line_match = re.match(
            r"(?i)^(?:\(?\s*([A-D])\s*\)?|option\s+([A-D]))[\.\)!]?$",
            last_line.strip(),
        )
        if last_line_match:
            letter = (last_line_match.group(1) or last_line_match.group(2)).upper()
            return _set_letter(parsed, letter, "last_line_letter", "medium", option_map)

    # 4. Unique option-text match. Useful when a model gives the answer text but no letter.
    if option_map:
        normalized_candidate = normalize_option_text(text)
        matched_labels = []

        for label, option_text in option_map.items():
            normalized_option = normalize_option_text(option_text)
            if normalized_option and normalized_option in normalized_candidate:
                matched_labels.append(label)

        matched_labels = _unique_preserving_order(matched_labels)

        if len(matched_labels) == 1:
            return _set_letter(parsed, matched_labels[0], "unique_option_text_match", "medium", option_map)

        if len(matched_labels) > 1:
            parsed["ambiguous"] = True
            parsed["notes"].append(f"multiple_option_text_matches:{','.join(matched_labels)}")
            return parsed

    # 5. Conservative tail fallback. Keep this low confidence for auditing.
    tail = text[-300:]
    tail_candidates = re.findall(
        r"(?i)(?:^|[\s\(\[])([A-D])(?:[\)\].,;:!\s]|$)",
        tail,
    )
    tail_candidates = [x.upper() for x in tail_candidates]
    tail_unique = _unique_preserving_order(tail_candidates)

    if len(tail_unique) == 1:
        parsed["notes"].append("used_low_confidence_tail_fallback")
        return _set_letter(parsed, tail_unique[0], "tail_letter", "low", option_map)

    if len(tail_unique) > 1:
        parsed["ambiguous"] = True
        parsed["notes"].append(f"ambiguous_tail_letters:{','.join(tail_unique)}")

    return parsed


def grade_science_candidate(candidate_text: Optional[str], raw_item: Dict[str, object]) -> bool:
    option_map = raw_item.get("option_map")
    if not isinstance(option_map, dict):
        option_map = extract_option_map_from_question(str(raw_item.get("question", "")))

    parsed = parse_science_candidate_answer(candidate_text, option_map)
    return parsed["letter"] == str(raw_item.get("ground_truth", "")).upper()