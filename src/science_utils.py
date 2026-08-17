import re
from typing import Dict, List, Optional


SCIENCE_FINAL_ANSWER_FORMAT = "FINAL ANSWER: <A, B, C, or D>"


def normalize_option_text(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\"'`*_]+", "", text)
    text = re.sub(r"\s*[\.,;:!?]+\s*$", "", text)
    return text


def render_science_question(question_stem: str, options: List[str]) -> str:
    lines = [question_stem.strip(), "Options:"]
    for idx, option_text in enumerate(options):
        lines.append(f"{chr(65 + idx)}. {option_text.strip()}")
    return "\n".join(lines) + "\n"


def build_option_map(options: List[str]) -> Dict[str, str]:
    return {chr(65 + idx): option.strip() for idx, option in enumerate(options)}


def validate_science_options(options: List[str]) -> List[str]:
    issues = []
    if len(options) != 4:
        issues.append(f"expected 4 options, found {len(options)}")

    normalized = [normalize_option_text(option) for option in options]
    if any(not option for option in normalized):
        issues.append("found an empty option")

    if len(set(normalized)) != len(normalized):
        issues.append("found duplicate option text after normalization")

    return issues


def extract_option_map_from_question(question_text: str) -> Dict[str, str]:
    option_map: Dict[str, str] = {}
    for match in re.finditer(r"(?im)^\s*([A-D])\.\s*(.+?)\s*$", question_text):
        option_map[match.group(1).upper()] = match.group(2).strip()
    return option_map


def parse_science_candidate_answer(
    candidate_text: Optional[str],
    option_map: Optional[Dict[str, str]] = None,
) -> Dict[str, Optional[str]]:
    parsed = {
        "letter": None,
        "option_text": None,
        "mode": None,
    }
    if not candidate_text:
        return parsed

    text = candidate_text.strip()
    upper_text = text.upper()

    letter_patterns = [
        r"FINAL ANSWER\s*[:\-]\s*\(?([A-D])\)?",
        r"CORRECT (?:OPTION|ANSWER)\s*(?:IS)?\s*[:\-]?\s*\(?([A-D])\)?",
        r"ANSWER\s*(?:IS)?\s*[:\-]?\s*\(?([A-D])\)?",
        r"OPTION\s*(?:IS)?\s*[:\-]?\s*\(?([A-D])\)?",
        r"THEREFORE[, ]+(?:THE )?(?:CORRECT )?(?:ANSWER|OPTION)\s*(?:IS)?\s*\(?([A-D])\)?",
    ]
    for pattern in letter_patterns:
        match = re.search(pattern, upper_text, flags=re.IGNORECASE)
        if match:
            parsed["letter"] = match.group(1).upper()
            parsed["mode"] = "letter_pattern"
            break

    if parsed["letter"] is None:
        tail = upper_text[-400:]
        standalone = re.findall(r"(?<![A-Z])([A-D])(?![A-Z])", tail)
        if standalone:
            parsed["letter"] = standalone[-1]
            parsed["mode"] = "tail_letter"

    if option_map:
        normalized_text = normalize_option_text(text)

        if parsed["letter"] and parsed["letter"] in option_map:
            parsed["option_text"] = option_map[parsed["letter"]]
            return parsed

        matched_labels = []
        for label, option_text in option_map.items():
            normalized_option = normalize_option_text(option_text)
            if normalized_option and normalized_option in normalized_text:
                matched_labels.append(label)

        if len(matched_labels) == 1:
            parsed["letter"] = matched_labels[0]
            parsed["option_text"] = option_map[parsed["letter"]]
            parsed["mode"] = parsed["mode"] or "option_text_match"
            return parsed

    if parsed["letter"] and option_map and parsed["letter"] in option_map:
        parsed["option_text"] = option_map[parsed["letter"]]

    return parsed