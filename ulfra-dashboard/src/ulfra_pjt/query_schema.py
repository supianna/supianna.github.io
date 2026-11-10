from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from ulfra_pjt.intent import ParsedQuestion, normalize_text, parse_question
from ulfra_pjt.queries import get_region
from ulfra_pjt.service_groups import get_service_group_names

QueryTask = Literal[
    "count_places",
    "list_places",
    "rank_regions",
    "compare_regions",
    "region_summary",
    "explain_metric",
]

VALID_AGE_COLUMNS = {
    "0s": "pop_0s",
    "10s": "pop_10s",
    "under_20": "pop_under_20",
    "20s": "pop_20s",
    "3040s": "pop_3040s",
    "5060s": "pop_5060s",
    "70over": "pop_70over",
}

VALID_GENDERS = {"male", "female"}
COUNT_KEYWORDS = ("몇개", "몇 개", "몇곳", "몇 곳", "개수", "수는", "얼마나")
LIST_KEYWORDS = ("목록", "리스트", "리스트화", "보여", "알려", "찾아", "후보")
RANK_KEYWORDS = (
    "추천",
    "제시",
    "순위",
    "많은",
    "많고",
    "상위",
    "좋은",
    "괜찮",
    "이사",
)
METRIC_KEYWORDS = ("점수", "공급점수", "뜻", "의미", "기준", "산식")


@dataclass(frozen=True)
class StructuredQuery:
    raw_question: str
    task: QueryTask
    region_ids: list[str] = field(default_factory=list)
    region_labels: list[str] = field(default_factory=list)
    service_groups: list[str] = field(default_factory=list)
    age_key: str | None = None
    age_label: str | None = None
    gender: str | None = None
    gender_label: str | None = None
    demographic_column: str | None = None
    demographic_label: str | None = None
    limit: int = 5
    needs_list: bool = False
    sort_basis: str = "demographic_then_service_count"
    review_flags: list[str] = field(default_factory=list)
    parsed: ParsedQuestion | None = None


def _extract_limit(question: str, default: int = 5) -> int:
    normalized = normalize_text(question)
    match = re.search(r"(\d{1,2})\s*(?:곳|개|군데|군대|동네)", normalized)
    if match:
        return max(1, min(int(match.group(1)), 10))
    if "세곳" in normalized or "세 곳" in normalized or "3곳" in normalized:
        return 3
    return default


def _determine_task(parsed: ParsedQuestion, question: str) -> QueryTask:
    normalized = normalize_text(question)
    has_count = any(keyword in normalized for keyword in COUNT_KEYWORDS)
    has_list = any(keyword in normalized for keyword in LIST_KEYWORDS)
    has_rank = any(keyword in normalized for keyword in RANK_KEYWORDS)
    has_metric = any(keyword in normalized for keyword in METRIC_KEYWORDS)

    if parsed.intent == "compare_regions":
        return "compare_regions"
    if has_count and parsed.region_ids and parsed.service_groups and not has_rank:
        return "count_places"
    if has_rank and (parsed.demographic_column or parsed.service_groups):
        return "rank_regions"
    if has_list and parsed.region_ids and parsed.service_groups:
        return "list_places"
    if has_metric:
        return "explain_metric"
    if parsed.intent in {"rank_regions", "place_candidates"}:
        return parsed.intent  # type: ignore[return-value]
    return "region_summary"


def structure_question(
    question: str,
    fallback_region_id: str | None = None,
    fallback_service_groups: list[str] | None = None,
) -> StructuredQuery:
    parsed = parse_question(question, fallback_region_id=fallback_region_id)
    service_groups = parsed.service_groups or fallback_service_groups or []
    task = _determine_task(
        ParsedQuestion(
            question=parsed.question,
            intent=parsed.intent,
            region_ids=parsed.region_ids,
            region_labels=parsed.region_labels,
            service_groups=service_groups,
            needs_child_context=parsed.needs_child_context,
            needs_young_context=parsed.needs_young_context,
            needs_place_candidates=parsed.needs_place_candidates,
            demographic_age_key=parsed.demographic_age_key,
            demographic_age_label=parsed.demographic_age_label,
            demographic_gender=parsed.demographic_gender,
            demographic_gender_label=parsed.demographic_gender_label,
            demographic_column=parsed.demographic_column,
            demographic_label=parsed.demographic_label,
        ),
        question,
    )
    return validate_structured_query(
        StructuredQuery(
            raw_question=question,
            task=task,
            region_ids=parsed.region_ids,
            region_labels=parsed.region_labels,
            service_groups=service_groups,
            age_key=parsed.demographic_age_key,
            age_label=parsed.demographic_age_label,
            gender=parsed.demographic_gender,
            gender_label=parsed.demographic_gender_label,
            demographic_column=parsed.demographic_column,
            demographic_label=parsed.demographic_label,
            limit=_extract_limit(question),
            needs_list=task in {"list_places", "rank_regions"},
            parsed=parsed,
        )
    )


def validate_structured_query(query: StructuredQuery) -> StructuredQuery:
    flags: list[str] = []
    valid_service_groups = set(get_service_group_names())

    for region_id in query.region_ids:
        if not get_region(region_id):
            flags.append("REGION_UNMAPPED")

    unknown_services = [
        service for service in query.service_groups if service not in valid_service_groups
    ]
    if unknown_services:
        flags.append("CATEGORY_UNMAPPED")

    if query.age_key and query.age_key not in VALID_AGE_COLUMNS:
        flags.append("AGE_UNMAPPED")

    if query.gender and query.gender not in VALID_GENDERS:
        flags.append("GENDER_UNMAPPED")

    if query.demographic_column:
        sample_region = get_region(query.region_ids[0]) if query.region_ids else None
        if sample_region and query.demographic_column not in sample_region:
            flags.append("DEMOGRAPHIC_COLUMN_UNMAPPED")

    if query.task in {"count_places", "list_places"} and not query.region_ids:
        flags.append("REGION_REQUIRED")

    if query.task in {"count_places", "list_places"} and not query.service_groups:
        flags.append("CATEGORY_REQUIRED")

    return StructuredQuery(
        raw_question=query.raw_question,
        task=query.task,
        region_ids=query.region_ids,
        region_labels=query.region_labels,
        service_groups=query.service_groups,
        age_key=query.age_key,
        age_label=query.age_label,
        gender=query.gender,
        gender_label=query.gender_label,
        demographic_column=query.demographic_column,
        demographic_label=query.demographic_label,
        limit=query.limit,
        needs_list=query.needs_list,
        sort_basis=query.sort_basis,
        review_flags=flags,
        parsed=query.parsed,
    )
