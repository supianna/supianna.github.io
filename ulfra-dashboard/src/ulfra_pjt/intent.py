from __future__ import annotations

import re
from dataclasses import dataclass, field

from ulfra_pjt.queries import get_regions
from ulfra_pjt.service_groups import get_service_group_names

SERVICE_SYNONYMS = {
    "병의원": ["병원", "의원", "내과", "소아과", "병의원", "의료"],
    "치과": ["치과", "치과의원"],
    "카페": ["카페", "커피", "까페"],
    "편의점": ["편의점"],
    "슈퍼마켓": ["슈퍼", "슈퍼마켓", "마트"],
    "한식": ["한식", "백반", "국밥"],
    "중식": ["중식", "중국집", "짜장", "짬뽕"],
    "일식": ["일식", "초밥", "스시", "라멘"],
    "양식": ["양식", "파스타", "스테이크"],
    "분식": ["분식", "김밥", "떡볶이"],
    "주점": ["호프", "호프집", "주점", "술집", "맥주", "생맥주", "포차"],
    "헬스장": ["헬스", "헬스장", "피트니스", "체력단련", "체육관", "운동할 곳", "운동"],
    "PC방": ["pc방", "피씨방", "피시방", "pc", "게임방", "인터넷방"],
}

AGE_RULES = {
    "0s": {
        "label": "0~9세",
        "keywords": ["0~9", "영유아", "영아", "유아", "아기", "어린이", "키즈"],
    },
    "10s": {
        "label": "10대",
        "keywords": ["10대", "10~19", "십대", "청소년", "중학생", "고등학생"],
    },
    "20s": {
        "label": "20대",
        "keywords": ["20대", "20~29"],
    },
    "3040s": {
        "label": "30~40대",
        "keywords": ["30대", "40대", "30~40", "3040"],
    },
    "5060s": {
        "label": "50~60대",
        "keywords": ["50대", "60대", "50~60", "5060"],
    },
    "70over": {
        "label": "70세 이상",
        "keywords": ["70대", "80대", "90대", "고령", "노년", "어르신"],
    },
}

GENDER_RULES = {
    "female": {
        "label": "여성",
        "keywords": ["여성", "여자", "여아", "여학생", "딸"],
    },
    "male": {
        "label": "남성",
        "keywords": ["남성", "남자", "남아", "남학생", "아들"],
    },
}

CHILD_KEYWORDS = ["유아", "아이", "아기", "어린이", "자녀", "가족", "키즈"]
YOUNG_KEYWORDS = ["젊은", "젊은층", "20대", "청년", "친구들"]
PLACE_KEYWORDS = [
    "가게",
    "장소",
    "후보",
    "목록",
    "리스트",
    "리스트화",
    "조사",
    "조회",
    "찾아",
    "보여",
    "알려",
    "추천",
]
COMPARE_KEYWORDS = ["비교", "차이", "대비"]
RANK_KEYWORDS = ["많은", "높은", "어디", "동네", "순위"]


@dataclass(frozen=True)
class ParsedQuestion:
    question: str
    intent: str
    region_ids: list[str] = field(default_factory=list)
    region_labels: list[str] = field(default_factory=list)
    service_groups: list[str] = field(default_factory=list)
    needs_child_context: bool = False
    needs_young_context: bool = False
    needs_place_candidates: bool = False
    demographic_age_key: str | None = None
    demographic_age_label: str | None = None
    demographic_gender: str | None = None
    demographic_gender_label: str | None = None
    demographic_column: str | None = None
    demographic_label: str | None = None


def normalize_text(text: str) -> str:
    return " ".join(text.strip().split()).lower()


def extract_regions(question: str) -> tuple[list[str], list[str]]:
    normalized_question = normalize_text(question)
    regions = get_regions()
    matched: list[tuple[str, str]] = []

    for row in regions.itertuples(index=False):
        dong_name = str(row.dong_name)
        gu_name = str(row.gu_name)
        candidates = {
            dong_name,
            f"{gu_name} {dong_name}",
            dong_name.replace("동", ""),
            dong_name.replace("읍", ""),
            dong_name.replace("면", ""),
        }
        if any(candidate and candidate.lower() in normalized_question for candidate in candidates):
            matched.append((row.region_id, f"{gu_name} {dong_name}"))

    unique_ids: list[str] = []
    unique_labels: list[str] = []
    for region_id, label in matched:
        if region_id not in unique_ids:
            unique_ids.append(region_id)
            unique_labels.append(label)

    return unique_ids, unique_labels


def extract_service_groups(question: str) -> list[str]:
    normalized_question = normalize_text(question)
    matched_groups: list[str] = []

    for service_group in get_service_group_names():
        keywords = SERVICE_SYNONYMS.get(service_group, [service_group])
        if any(keyword.lower() in normalized_question for keyword in keywords):
            matched_groups.append(service_group)

    return matched_groups


def extract_demographic_condition(
    question: str,
) -> tuple[str | None, str | None, str | None, str | None, str | None, str | None]:
    normalized_question = normalize_text(question)
    age_key = None
    age_label = None
    gender = None
    gender_label = None

    if "10대 이하" in normalized_question or "19세 이하" in normalized_question:
        age_key = "under_20"
        age_label = "10대 이하"

    age_match = re.search(r"(\d{1,3})\s*세", normalized_question)
    if age_match and not age_key:
        age = int(age_match.group(1))
        if age < 10:
            age_key = "0s"
        elif age < 20:
            age_key = "10s"
        elif age < 30:
            age_key = "20s"
        elif age < 50:
            age_key = "3040s"
        elif age < 70:
            age_key = "5060s"
        else:
            age_key = "70over"
        age_label = AGE_RULES[age_key]["label"]
    elif not age_key:
        for candidate_age_key, rule in AGE_RULES.items():
            if any(keyword.lower() in normalized_question for keyword in rule["keywords"]):
                age_key = candidate_age_key
                age_label = rule["label"]
                break

    for candidate_gender, rule in GENDER_RULES.items():
        if any(keyword.lower() in normalized_question for keyword in rule["keywords"]):
            gender = candidate_gender
            gender_label = rule["label"]
            break

    if age_key == "under_20":
        column = "pop_under_20"
        label = age_label
    elif age_key and gender:
        column = f"pop_{age_key}_{gender}"
        label = f"{age_label} {gender_label}"
    elif age_key:
        column = f"pop_{age_key}"
        label = age_label
    elif gender:
        column = f"{gender}_pop"
        label = gender_label
    else:
        column = None
        label = None

    return age_key, age_label, gender, gender_label, column, label


def parse_question(question: str, fallback_region_id: str | None = None) -> ParsedQuestion:
    normalized_question = normalize_text(question)
    region_ids, region_labels = extract_regions(question)
    if not region_ids and fallback_region_id:
        fallback_regions = get_regions()
        matched = fallback_regions[fallback_regions["region_id"] == fallback_region_id]
        if not matched.empty:
            row = matched.iloc[0]
            region_ids = [fallback_region_id]
            region_labels = [f"{row['gu_name']} {row['dong_name']}"]

    service_groups = extract_service_groups(question)
    (
        demographic_age_key,
        demographic_age_label,
        demographic_gender,
        demographic_gender_label,
        demographic_column,
        demographic_label,
    ) = extract_demographic_condition(question)
    needs_child_context = (
        demographic_age_key == "0s"
        or (
            demographic_age_key is None
            and any(keyword in normalized_question for keyword in CHILD_KEYWORDS)
        )
    )
    needs_young_context = demographic_age_key == "20s" or any(
        keyword in normalized_question for keyword in YOUNG_KEYWORDS
    )
    needs_place_candidates = any(keyword in normalized_question for keyword in PLACE_KEYWORDS)

    if len(region_ids) >= 2 or any(keyword in normalized_question for keyword in COMPARE_KEYWORDS):
        intent = "compare_regions"
    elif (
        demographic_column or needs_young_context
    ) and any(keyword in normalized_question for keyword in RANK_KEYWORDS):
        intent = "rank_regions"
    elif needs_place_candidates:
        intent = "place_candidates"
    else:
        intent = "region_summary"

    return ParsedQuestion(
        question=question,
        intent=intent,
        region_ids=region_ids,
        region_labels=region_labels,
        service_groups=service_groups,
        needs_child_context=needs_child_context,
        needs_young_context=needs_young_context,
        needs_place_candidates=needs_place_candidates,
        demographic_age_key=demographic_age_key,
        demographic_age_label=demographic_age_label,
        demographic_gender=demographic_gender,
        demographic_gender_label=demographic_gender_label,
        demographic_column=demographic_column,
        demographic_label=demographic_label,
    )
