from __future__ import annotations

import re
from typing import Any

import pandas as pd

from ulfra_pjt.analytics import calculate_age_distribution, calculate_service_density
from ulfra_pjt.intent import ParsedQuestion, normalize_text, parse_question
from ulfra_pjt.queries import (
    _build_service_group_filter,
    count_places_by_category_ids,
    get_category_options,
    get_places,
    get_places_by_category_ids,
    get_region,
    get_region_service_counts,
    get_regions,
    read_dataframe,
    search_places,
)
from ulfra_pjt.query_schema import structure_question

AGE_PROXY_COLUMNS = {
    "child": "0~9세",
    "young": "20~29세",
}

SERVICE_KEYWORD_FALLBACKS = {
    "분식": ["분식", "김밥", "떡볶이", "라면", "만두", "튀김"],
    "카페": ["카페", "커피", "까페"],
    "주점": ["호프", "주점", "맥주", "포차"],
}

CATEGORY_STOPWORDS = {
    "개수",
    "궁금",
    "근처",
    "기준",
    "동네",
    "리스트",
    "목록",
    "많아",
    "많은",
    "보여",
    "수는",
    "순위",
    "알려",
    "어디",
    "얼마나",
    "있는지",
    "정도",
    "주변",
    "추천",
    "후보",
}
RANK_REQUEST_WORDS = ("추천", "순위", "많은", "많고", "상위", "어디", "좋은")
DYNAMIC_COUNT_WORDS = ("몇", "개수", "수는", "얼마나")
DYNAMIC_LIST_WORDS = ("목록", "리스트", "보여", "알려", "찾아", "후보", "어디", "있어")


def _region_label(region: dict[str, Any]) -> str:
    return f"{region['gu_name']} {region['dong_name']}"


def _demographic_population(region: dict[str, Any], column: str) -> int:
    if column == "pop_under_20":
        return int(region["pop_0s"]) + int(region["pop_10s"])
    return int(region[column])


def _service_groups_or_default(parsed: ParsedQuestion, fallback: list[str] | None) -> list[str]:
    if parsed.service_groups:
        return parsed.service_groups
    if fallback:
        return fallback
    if parsed.demographic_column:
        return []
    return ["카페", "편의점", "병의원"]


def _places_preview(region_id: str, service_groups: list[str], limit: int = 8) -> list[dict[str, Any]]:
    if not service_groups:
        return []

    places = get_places(region_id, service_groups, limit=limit)
    preview: list[dict[str, Any]] = []

    for row in places.itertuples(index=False):
        preview.append(
            {
                "name": row.name,
                "branch_name": row.branch_name,
                "address": row.address,
                "service_group_proxy": ", ".join(service_groups),
                "category_id": row.category_id,
                "sub_group": row.sub_group,
                "sub_name": row.sub_name,
            }
        )

    return preview


def _keyword_place_preview(
    region_id: str,
    service_groups: list[str],
    limit: int = 8,
) -> list[dict[str, Any]]:
    keywords: list[str] = []
    for service_group in service_groups:
        keywords.extend(SERVICE_KEYWORD_FALLBACKS.get(service_group, []))

    preview: list[dict[str, Any]] = []
    seen_place_ids: set[str] = set()

    for keyword in keywords:
        places = search_places(keyword, region_id=region_id, limit=limit)
        for row in places.itertuples(index=False):
            if row.place_id in seen_place_ids:
                continue
            seen_place_ids.add(row.place_id)
            preview.append(
                {
                    "name": row.name,
                    "branch_name": row.branch_name,
                    "address": row.address,
                    "keyword": keyword,
                    "candidate_basis": "상호명 키워드 보조 후보",
                    "category_id": row.category_id,
                    "sub_group": row.sub_group,
                    "sub_name": row.sub_name,
                }
            )
            if len(preview) >= limit:
                return preview

    return preview


def _question_category_tokens(question: str, region_labels: list[str]) -> list[str]:
    normalized = normalize_text(question)
    for label in region_labels:
        for part in label.split():
            normalized = normalized.replace(part.lower(), " ")

    tokens = re.findall(r"[0-9a-zA-Z가-힣]+", normalized)
    return [
        token
        for token in tokens
        if len(token) >= 2 and token not in CATEGORY_STOPWORDS
    ]


def _category_matches_from_question(
    question: str,
    region_labels: list[str],
    service_groups: list[str],
    limit: int = 8,
) -> list[dict[str, Any]]:
    if service_groups:
        return []

    normalized = normalize_text(question)
    tokens = _question_category_tokens(question, region_labels)
    if not tokens:
        return []

    categories = get_category_options()
    matches: list[dict[str, Any]] = []

    for row in categories.itertuples(index=False):
        main_group = str(row.main_group)
        sub_group = str(row.sub_group)
        sub_name = str(row.sub_name)
        searchable = {
            "main_group": normalize_text(main_group),
            "sub_group": normalize_text(sub_group),
            "sub_name": normalize_text(sub_name),
        }
        score = 0

        if searchable["sub_name"] and searchable["sub_name"] in normalized:
            score += 100
        if searchable["sub_group"] and searchable["sub_group"] in normalized:
            score += 40
        if searchable["main_group"] and searchable["main_group"] in normalized:
            score += 10

        for token in tokens:
            if token in searchable["sub_name"]:
                score += 20
            if token in searchable["sub_group"]:
                score += 8
            if token in searchable["main_group"]:
                score += 4
            if searchable["sub_name"] and searchable["sub_name"] in token:
                score += 30

        if score:
            matches.append(
                {
                    "category_id": row.category_id,
                    "main_group": main_group,
                    "sub_group": sub_group,
                    "sub_name": sub_name,
                    "score": score,
                }
            )

    ranked = sorted(matches, key=lambda item: (-item["score"], item["category_id"]))
    return ranked[:limit]


def _category_ids(category_matches: list[dict[str, Any]]) -> list[str]:
    return [category["category_id"] for category in category_matches]


def _dynamic_category_label(category_matches: list[dict[str, Any]]) -> str:
    names = [category["sub_name"] for category in category_matches]
    return ", ".join(names[:5])


def _dynamic_category_preview(
    region_id: str,
    category_matches: list[dict[str, Any]],
    limit: int = 8,
) -> list[dict[str, Any]]:
    places = get_places_by_category_ids(region_id, _category_ids(category_matches), limit=limit)
    preview: list[dict[str, Any]] = []

    for row in places.itertuples(index=False):
        preview.append(
            {
                "name": row.name,
                "branch_name": row.branch_name,
                "address": row.address,
                "category_id": row.category_id,
                "sub_group": row.sub_group,
                "sub_name": row.sub_name,
            }
        )

    return preview


def _region_fact(
    region_id: str,
    service_groups: list[str],
    parsed: ParsedQuestion | None = None,
    category_matches: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    region = get_region(region_id)
    if not region:
        return None

    age_distribution = calculate_age_distribution(region)
    service_counts = get_region_service_counts(region_id)
    service_density = calculate_service_density(region, service_counts)
    selected_services = service_density[
        service_density["service_group"].isin(service_groups)
    ].copy()

    demographic_fact = None
    if parsed and parsed.demographic_column and parsed.demographic_label:
        demographic_population = _demographic_population(region, parsed.demographic_column)
        demographic_fact = {
            "label": parsed.demographic_label,
            "column": parsed.demographic_column,
            "population": demographic_population,
            "ratio": round(demographic_population / int(region["total_pop"]) * 100, 1),
        }

    dynamic_category = None
    category_matches = category_matches or []
    if category_matches:
        place_count = count_places_by_category_ids(region_id, _category_ids(category_matches))
        total_pop = int(region["total_pop"])
        dynamic_category = {
            "label": _dynamic_category_label(category_matches),
            "matched_categories": [
                {
                    "category_id": category["category_id"],
                    "main_group": category["main_group"],
                    "sub_group": category["sub_group"],
                    "sub_name": category["sub_name"],
                }
                for category in category_matches
            ],
            "place_count": place_count,
            "places_per_1000": round(place_count / total_pop * 1000, 2)
            if total_pop
            else 0.0,
            "place_candidates": _dynamic_category_preview(region_id, category_matches),
        }

    return {
        "region": {
            "region_id": region["region_id"],
            "label": _region_label(region),
            "gu_name": region["gu_name"],
            "dong_name": region["dong_name"],
            "total_pop": int(region["total_pop"]),
        },
        "selected_demographic": demographic_fact,
        "age_distribution": [
            {
                "age_group": row.age_group,
                "population": int(row.population),
                "ratio": round(float(row.ratio), 1),
            }
            for row in age_distribution.itertuples(index=False)
        ],
        "selected_service_groups": [
            {
                "service_group": row.service_group,
                "place_count": int(row.place_count),
                "places_per_1000": round(float(row.places_per_1000), 2),
            }
            for row in selected_services.itertuples(index=False)
        ],
        "place_candidates": _places_preview(region_id, service_groups),
        "keyword_place_candidates": _keyword_place_preview(region_id, service_groups),
        "dynamic_category": dynamic_category,
    }


def _rank_regions_by_demographic_and_service(
    parsed: ParsedQuestion,
    service_groups: list[str],
    category_matches: list[dict[str, Any]] | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    regions = get_regions()
    demographic_column = parsed.demographic_column
    demographic_label = parsed.demographic_label
    category_matches = category_matches or []
    category_ids = _category_ids(category_matches)

    if category_ids:
        place_counts = {
            row.region_id: count_places_by_category_ids(row.region_id, category_ids)
            for row in regions.itertuples(index=False)
        }
    elif service_groups:
        filter_sql, params = _build_service_group_filter(service_groups)
        sql = f"""
            SELECT p.region_id, COUNT(*) AS place_count
            FROM places p
            JOIN categories c ON p.category_id = c.category_id
            WHERE 1=1 {filter_sql}
            GROUP BY p.region_id
        """
        df_counts = read_dataframe(sql, params)
        place_counts = dict(zip(df_counts["region_id"], df_counts["place_count"]))
    else:
        place_counts = {}

    dynamic_label = _dynamic_category_label(category_matches) if category_matches else None

    for row in regions.itertuples(index=False):
        region = get_region(row.region_id)
        selected_count = place_counts.get(row.region_id, 0)
        demographic_population = (
            _demographic_population(region, demographic_column)
            if demographic_column
            else None
        )
        demographic_ratio = (
            demographic_population / int(region["total_pop"]) * 100
            if demographic_population is not None
            else None
        )
        rows.append(
            {
                "region_id": row.region_id,
                "region_label": f"{row.gu_name} {row.dong_name}",
                "total_pop": int(region["total_pop"]),
                "demographic_label": demographic_label,
                "demographic_column": demographic_column,
                "demographic_population": demographic_population,
                "demographic_ratio": round(demographic_ratio, 1)
                if demographic_ratio is not None
                else None,
                "pop_20s": int(region["pop_20s"]),
                "pop_20s_ratio": round(int(region["pop_20s"]) / int(region["total_pop"]) * 100, 1),
                "selected_service_place_count": selected_count,
                "dynamic_category_label": dynamic_label,
            }
        )

    sort_columns = (
        ["demographic_population", "selected_service_place_count"]
        if demographic_column
        else ["selected_service_place_count", "total_pop"]
    )
    ranked = pd.DataFrame(rows).sort_values(sort_columns, ascending=[False, False])
    top_candidates = ranked.head(limit).to_dict(orient="records")
    for item in top_candidates:
        item["place_candidates"] = (
            _dynamic_category_preview(item["region_id"], category_matches, limit=3)
            if category_matches
            else _places_preview(item["region_id"], service_groups, limit=3)
        )
        item["keyword_place_candidates"] = _keyword_place_preview(
            item["region_id"],
            service_groups,
            limit=3,
        )
    return top_candidates


def build_question_fact_pack(
    question: str,
    fallback_region_id: str | None = None,
    fallback_service_groups: list[str] | None = None,
) -> dict[str, Any]:
    structured_query = structure_question(
        question,
        fallback_region_id=fallback_region_id,
        fallback_service_groups=fallback_service_groups,
    )
    parsed = structured_query.parsed or parse_question(
        question,
        fallback_region_id=fallback_region_id,
    )
    category_matches = _category_matches_from_question(
        question,
        structured_query.region_labels,
        structured_query.service_groups,
    )
    service_groups = structured_query.service_groups or (
        [] if category_matches else _service_groups_or_default(parsed, fallback_service_groups)
    )
    task = structured_query.task
    normalized_question = normalize_text(question)
    if category_matches and structured_query.region_ids:
        if any(word in normalized_question for word in DYNAMIC_COUNT_WORDS):
            task = "count_places"
        elif any(word in normalized_question for word in DYNAMIC_LIST_WORDS):
            task = "place_candidates"
    if (
        category_matches
        and not structured_query.region_ids
        and any(word in normalized_question for word in RANK_REQUEST_WORDS)
    ):
        task = "rank_regions"

    facts: dict[str, Any] = {
        "question": question,
        "intent": task,
        "query_schema": {
            "task": task,
            "region_labels": structured_query.region_labels,
            "service_groups": service_groups,
            "category_matches": [
                {
                    "category_id": category["category_id"],
                    "main_group": category["main_group"],
                    "sub_group": category["sub_group"],
                    "sub_name": category["sub_name"],
                }
                for category in category_matches
            ],
            "demographic_label": structured_query.demographic_label,
            "demographic_column": structured_query.demographic_column,
            "limit": structured_query.limit,
            "review_flags": structured_query.review_flags,
        },
        "parsed": {
            "regions": structured_query.region_labels,
            "service_groups": service_groups,
            "category_matches": [
                category["sub_name"] for category in category_matches
            ],
            "needs_child_context": parsed.needs_child_context,
            "needs_young_context": parsed.needs_young_context,
            "needs_place_candidates": parsed.needs_place_candidates,
            "demographic_label": structured_query.demographic_label,
            "demographic_column": structured_query.demographic_column,
        },
        "answer_policy": {
            "direct_facts": "DB에서 조회된 지역/업종/인구/시설 수만 확정 사실로 사용",
            "proxy_facts": [],
            "must_not_claim": [
                "리뷰, 평점, 매출, 방문량, 실제 손님 연령대",
                "유아 동반 가능 여부, 유아 의자, 놀이공간, 주차 가능 여부",
                "맛집, 인기 1위, 젊은 손님이 실제로 많다는 단정",
            ],
        },
        "data_scope": {
            "commercial_data_date": "2026-06",
            "population_data_date": "2026-08-31",
            "region_unit": "울산 행정동",
        },
    }

    if parsed.needs_child_context:
        facts["answer_policy"]["proxy_facts"].append(
            "유아 관련 질문은 0~9세 거주 인구 비율만 proxy로 사용"
        )

    if parsed.needs_young_context:
        facts["answer_policy"]["proxy_facts"].append(
            "젊은 층 관련 질문은 20~29세 거주 인구 비율만 proxy로 사용"
        )

    if parsed.demographic_column and parsed.demographic_label:
        facts["answer_policy"]["proxy_facts"].append(
            f"{parsed.demographic_label} 관련 질문은 {parsed.demographic_column} 거주 인구를 기준으로 사용"
        )

    if structured_query.review_flags:
        facts["answer_policy"]["review_flags"] = structured_query.review_flags

    if task == "rank_regions":
        facts["ranked_region_candidates"] = _rank_regions_by_demographic_and_service(
            parsed,
            service_groups,
            category_matches=category_matches,
            limit=structured_query.limit,
        )
        return facts

    region_facts = []
    for region_id in structured_query.region_ids:
        region_fact = _region_fact(
            region_id,
            service_groups,
            parsed,
            category_matches=category_matches,
        )
        if region_fact:
            region_facts.append(region_fact)

    facts["region_facts"] = region_facts
    if not region_facts:
        facts["unsupported_reason"] = "질문에서 DB 행정동과 매칭되는 지역을 찾지 못했습니다."

    return facts


def build_template_answer(fact_pack: dict[str, Any]) -> str:
    """API 호출 전에도 보여줄 수 있는 빠른 DB 근거 답변입니다."""
    lines = [
        "### DB 기준으로 확인해봤어요",
        "먼저 결론부터 정리하면, 아래 내용은 프로젝트 DB에 기록된 인구와 시설 자료를 기준으로 본 결과입니다.",
    ]

    for proxy in fact_pack["answer_policy"]["proxy_facts"]:
        lines.append(f"- 기준: {proxy}")

    if fact_pack.get("unsupported_reason"):
        lines.append(f"- 지금은 바로 확인하기 어려워요: {fact_pack['unsupported_reason']}")
        return "\n".join(lines)

    if fact_pack["intent"] == "rank_regions":
        for region in fact_pack.get("ranked_region_candidates", []):
            category_label = region.get("dynamic_category_label") or "질문한 업종"
            if region["demographic_label"]:
                lines.append(
                    "- 먼저 볼 만한 동네는 "
                    f"{region['region_label']}입니다. "
                    f"{region['demographic_label']} "
                    f"{region['demographic_population']:,}명"
                    f"({region['demographic_ratio']}%)이고, "
                    f"{category_label}은 {region['selected_service_place_count']}곳으로 집계됩니다."
                )
            else:
                lines.append(
                    "- 먼저 볼 만한 동네는 "
                    f"{region['region_label']}입니다. "
                    f"{category_label}은 {region['selected_service_place_count']}곳으로 집계됩니다."
                )
            if region["place_candidates"]:
                place_names = [place["name"] for place in region["place_candidates"][:3]]
                lines.append(f"  - 업종 기준 후보 예시: {', '.join(place_names)}")
            elif region["keyword_place_candidates"]:
                place_names = [
                    place["name"] for place in region["keyword_place_candidates"][:3]
                ]
                lines.append(
                    "  - 상호명으로 넓혀 본 보조 후보: "
                    f"{', '.join(place_names)}"
                )
        lines.append("- 다만 실제 방문객 연령대나 인기 정보는 현재 DB에 없어서 단정하지 않았습니다.")
        lines.append("- 상호명 키워드 검색은 확정 업종이 아니라 참고용 후보로만 봐주세요.")
        return "\n".join(lines)

    for region_fact in fact_pack.get("region_facts", []):
        region = region_fact["region"]
        lines.append(f"- {region['label']} 기준으로 보면 총인구는 {region['total_pop']:,}명입니다.")
        if region_fact["selected_demographic"]:
            demographic = region_fact["selected_demographic"]
            lines.append(
                f"- 질문에 나온 연령대는 {demographic['label']}로 해석했고, "
                f"해당 인구는 {demographic['population']:,}명({demographic['ratio']}%)입니다."
            )
        for service in region_fact["selected_service_groups"]:
            lines.append(
                f"- {service['service_group']}은 {service['place_count']:,}곳입니다. "
                f"인구 1,000명당으로 보면 {service['places_per_1000']:.2f}곳이에요."
            )
        dynamic_category = region_fact.get("dynamic_category")
        if dynamic_category:
            matched_names = [
                category["sub_name"]
                for category in dynamic_category["matched_categories"][:5]
            ]
            lines.append(
                "- 질문한 업종은 DB 원천 카테고리 중 "
                f"{', '.join(matched_names)}로 해석했습니다."
            )
            lines.append(
                f"- {dynamic_category['label']}은 "
                f"{dynamic_category['place_count']:,}곳입니다. "
                f"인구 1,000명당으로 보면 "
                f"{dynamic_category['places_per_1000']:.2f}곳이에요."
            )
            if dynamic_category["place_candidates"]:
                place_names = [
                    place["name"]
                    for place in dynamic_category["place_candidates"][:8]
                ]
                lines.append(
                    "- DB 카테고리 기준으로 바로 보여줄 수 있는 후보는 "
                    f"{', '.join(place_names)}입니다."
                )
        if region_fact["place_candidates"]:
            place_names = [place["name"] for place in region_fact["place_candidates"][:8]]
            lines.append(f"- 업종 기준으로 바로 보여줄 수 있는 후보는 {', '.join(place_names)}입니다.")
        elif region_fact["keyword_place_candidates"]:
            place_names = [
                place["name"] for place in region_fact["keyword_place_candidates"][:8]
            ]
            lines.append(f"- 업종 기준 결과가 부족해서 상호명으로 넓혀 보면 {', '.join(place_names)}가 보입니다.")

    lines.append("- 참고로 유아 동반 가능 여부, 실제 방문객 연령대, 리뷰나 평점은 현재 DB에 없습니다.")
    return "\n".join(lines)
