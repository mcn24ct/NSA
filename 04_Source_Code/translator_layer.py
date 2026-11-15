"""Bilingual Vietnamese-English query translator with NASA glossary and Qwen3-8B integration."""

import re
from typing import Any, Final

import requests

import config

MAX_QUERY_CHARS: Final[int] = 256

VIETNAMESE_CHAR_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]",
    flags=re.IGNORECASE,
)

NASA_VI_EN_GLOSSARY: Final[dict[str, str]] = {
    "vi trọng lực": "microgravity 0g",
    "không trọng lực": "zero-gravity microgravity",
    "trọng lực một phần": "partial gravity",
    "căn cứ mặt trăng": "Lunar Base",
    "mặt trăng": "Lunar Base partial gravity",
    "bộ đồ vũ trụ": "Spacesuit EVA",
    "áo phi hành gia": "Spacesuit EVA",
    "trạm vũ trụ quốc tế": "ISS spacecraft",
    "ngọn lửa lạnh": "cool flame",
    "lửa lạnh": "cool flame",
    "tốc độ cháy lan": "flame spread rate",
    "tốc độ lan truyền ngọn lửa": "flame spread rate",
    "tốc độ cháy": "burn rate regression rate",
    "điểm bốc khói": "smoke point",
    "điểm khói": "smoke point",
    "dập tắt": "extinguishment suppression quenching",
    "tự tắt": "radiative extinction quenching",
    "chữa cháy": "fire suppression extinguishment",
    "đối lưu": "buoyancy convection",
    "bức xạ": "radiative heat loss",
    "vật liệu rắn": "solid fuel material PMMA cotton Nomex",
    "giọt nhiên liệu": "liquid droplet n-heptane methanol",
    "áp suất": "chamber pressure kPa psia atm",
    "nồng độ oxy": "oxygen concentration percentage % O2",
    "giới hạn oxy": "Limiting Oxygen Index LOI",
    "oxy": "oxygen % O2",
    "tốc độ gió": "forced airflow velocity mm/s cm/s",
    "luồng khí": "airflow velocity forced flow",
    "ngọn lửa cầu": "spherical flame symmetry",
    "bồ hóng": "soot shell concentration",
    "an toàn cháy": "spacecraft fire safety",
    "phòng ngừa": "fire prevention",
    "phát hiện": "smoke fire detection",
    "thí nghiệm cháy": "combustion experiment",
    "thí nghiệm": "experiment investigation",
    "nhiệt độ": "temperature Kelvin",
}

TRANSLATOR_SYSTEM_PROMPT: Final[str] = (
    "You are a NASA Microgravity Combustion terminology translator. "
    "Translate the Vietnamese user query into a concise, keyword-rich English search query "
    "optimized for BAAI/bge-small-en-v1.5 dense retrieval. Preserve exact NASA terms such as "
    "microgravity, Lunar Base, Spacesuit, cool flame, flame spread rate, smoke point, "
    "extinguishment, kPa, % O2, and mm/s. Output ONLY the translated English query string."
)


def contains_vietnamese(text: str) -> bool:
    """Return True if text contains Vietnamese diacritics or known Vietnamese phrases."""
    if VIETNAMESE_CHAR_PATTERN.search(text):
        return True
    lowered = text.lower()
    return any(vi_term in lowered for vi_term in NASA_VI_EN_GLOSSARY)


def extract_glossary_matches(query: str) -> list[str]:
    """Extract ordered NASA English technical terms matched from the Vietnamese query."""
    lowered = query.lower()
    matched: list[str] = []
    for vi_phrase in sorted(NASA_VI_EN_GLOSSARY.keys(), key=len, reverse=True):
        if vi_phrase in lowered:
            en_term = NASA_VI_EN_GLOSSARY[vi_phrase]
            if en_term not in matched:
                matched.append(en_term)
            lowered = lowered.replace(vi_phrase, " ")
    return matched


def build_dictionary_fallback_query(query: str, matched_terms: list[str]) -> str:
    """Construct an English BGE-optimized query using glossary mappings and preserved ASCII tokens."""
    ascii_tokens = re.findall(r"\b[A-Za-z0-9_.\-%/]+\b", query)
    vi_stopwords = {
        "va",
        "cua",
        "cac",
        "tren",
        "trong",
        "voi",
        "cho",
        "la",
        "co",
        "nhung",
        "mot",
        "nhu",
        "the",
        "nao",
    }
    preserved = [
        tok
        for tok in ascii_tokens
        if tok.lower() not in vi_stopwords and (any(c.isdigit() for c in tok) or len(tok) >= 2)
    ]
    parts = list(matched_terms)
    for tok in preserved:
        if not any(tok.lower() in p.lower() for p in parts):
            parts.append(tok)
    if not parts:
        return "NASA microgravity combustion experiment pressure kPa oxygen % O2 flame spread rate mm/s"
    return " ".join(parts).strip()


def _strip_think_tags(text: str) -> str:
    """Remove any residual <think> blocks and surrounding quotes from LLM output."""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip().strip('"').strip("'")


def _call_qwen_translator(
    query: str, matched_terms: list[str], timeout_sec: float = 1.8
) -> str | None:
    """Call local Qwen3-8B server with /no_think to translate Vietnamese query under 2 seconds."""
    glossary_hint = ", ".join(matched_terms) if matched_terms else "microgravity, combustion"
    user_prompt = (
        f"Vietnamese query: {query}\n"
        f"Mandatory NASA terms to include: {glossary_hint}\n"
        "English search query:\n/no_think"
    )
    payload: dict[str, Any] = {
        "messages": [
            {"role": "system", "content": TRANSLATOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 96,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    try:
        response = requests.post(
            f"{config.SERVER_BASE_URL}/v1/chat/completions",
            json=payload,
            timeout=timeout_sec,
        )
        response.raise_for_status()
        data = response.json()
        raw_content = str(data["choices"][0]["message"]["content"])
        cleaned = _strip_think_tags(raw_content)
        return cleaned if cleaned else None
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return None


def translate_to_english_query(query: str) -> dict[str, Any]:
    """Translate Vietnamese query to English for bge-small-en-v1.5 or return English unchanged."""
    clean_query = query.strip()[:MAX_QUERY_CHARS]
    if not clean_query or not contains_vietnamese(clean_query):
        return {
            "original_query": clean_query,
            "translated_query": clean_query[:MAX_QUERY_CHARS],
            "is_translated": False,
            "method": "passthrough",
            "matched_terms": [],
        }

    matched_terms = extract_glossary_matches(clean_query)
    llm_translated = _call_qwen_translator(clean_query, matched_terms)

    if llm_translated:
        missing_core = [
            term for term in matched_terms if term.split()[0].lower() not in llm_translated.lower()
        ]
        final_query = (
            f"{llm_translated} {' '.join(missing_core)}".strip()
            if missing_core
            else llm_translated
        )
        method = "qwen3_8b"
    else:
        final_query = build_dictionary_fallback_query(clean_query, matched_terms)
        method = "dictionary_fallback"

    final_query = final_query[:MAX_QUERY_CHARS].strip()
    return {
        "original_query": clean_query,
        "translated_query": final_query,
        "is_translated": True,
        "method": method,
        "matched_terms": matched_terms,
    }
