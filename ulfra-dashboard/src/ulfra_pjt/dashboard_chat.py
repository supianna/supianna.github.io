"""점수·비교와 같은 스냅샷에 근거하는 질문 응답 서비스."""

from typing import Any

from ulfra_pjt.dashboard_data import find_region, list_places
from ulfra_pjt.facts import build_question_fact_pack, build_template_answer
from ulfra_pjt.query_schema import structure_question
from ulfra_pjt.scoring import CATEGORIES

KEYWORDS = {
    "medical": ("병원", "의원", "병의원", "의료"),
    "food": ("식당", "음식", "외식", "맛집"),
    "cafe": ("카페", "커피"),
    "shop": ("쇼핑", "마트", "편의점", "소매"),
}

def build_chat_facts(
    snapshot: dict, question: str, region_ids: list[str], db_path=None
) -> dict:
    # 법정동 이름을 행정동으로 추측해서 바꾸지 않습니다. 정확한 등록 명칭만 대응합니다.
    matched = [r for r in snapshot["regions"] if r["dong_name"] in question]
    ambiguous = {
        r["dong_name"]
        for r in matched
        if sum(x["dong_name"] == r["dong_name"] for x in matched) > 1
    }
    matched = [
        r
        for r in matched
        if r["dong_name"] not in ambiguous or r["gu_name"] in question
    ]
    ids = [r["region_id"] for r in matched][:4] or region_ids
    regions = [find_region(snapshot, region_id) for region_id in ids]
    keys = [
        key
        for key, words in KEYWORDS.items()
        if any(word in question for word in words)
    ]
    keys = keys or list(CATEGORIES)
    # 질문에 지정된 부문이 여러 개면 해당 부문 점수의 단순평균으로 후보를 정렬합니다.
    ranked = sorted(
        snapshot["regions"],
        key=lambda r: (-sum(r["categories"][k]["score"] for k in keys), r["region_id"]),
    )
    candidates = [
        {
            "region_id": r["region_id"],
            "label": f"{r['gu_name']} {r['dong_name']}",
            "score": r["score"],
            "rank": r["rank"],
            "selected_category_score": sum(r["categories"][k]["score"] for k in keys)
            / len(keys),
        }
        for r in ranked[:5]
    ]
    places = []
    if any(word in question for word in ("목록", "가게", "주소", "어디", "장소")):
        category = keys[0] if len(keys) == 1 else "all"
        for r in regions[:2]:
            places.append(
                list_places(r["region_id"], category=category, limit=5, db_path=db_path)
            )
    return {
        "metadata": snapshot["metadata"],
        "metric_definitions": {
            "total_pop": "주민 수 (명)",
            "count": "시설 수 (개)",
            "per_1000": "인구 천 명당 시설 수 (개). 주민 수가 아님",
            "score": "상대적 공급점수 (점). 만족도나 백분율이 아님",
            "rank": "울산 전체 읍면동 중 공동 순위를 적용한 순위 (위)",
        },
        "regions": regions,
        "selected_categories": [CATEGORIES[k]["label"] for k in keys],
        "candidate_rule": "질문에서 지정한 부문 공급점수의 단순평균 내림차순 (공동값은 코드순)",
        "candidates": candidates,
        "place_previews": places,
        "unresolved_region_names": sorted(ambiguous) if not matched else [],
        "instructions": "점수는 계산된 값을 그대로 인용한다. 공원·학군·보행·안전·집값·영업 여부는 자료가 없다.",
    }


def database_answer(facts: dict, question: str) -> str:
    rows = []
    if facts["unresolved_region_names"]:
        rows.append(
            "같은 동 이름이 여러 구에 있습니다. 구·군까지 입력해 주세요. 아래는 화면 선택 지역입니다."
        )
    if "성남동" in question:
        rows.append(
            "성남동은 현재 행정동 목록에 없습니다. 다른 행정동으로 임의 변환하지 않았습니다."
        )
    for r in facts["regions"]:
        counts = " · ".join(
            f"{rule['label']} {r['categories'][key]['count']:,}개"
            for key, rule in CATEGORIES.items()
        )
        rows.append(
            f"{r['gu_name']} {r['dong_name']}: 공급점수 {r['score']:.1f}점, "
            f"울산 {r['rank']}위 / {facts['metadata']['region_count']}개 읍면동. "
            f"인구 {r['total_pop']:,}명. {counts}."
        )
        for key, rule in CATEGORIES.items():
            if any(word in question for word in KEYWORDS[key]):
                metric = r["categories"][key]
                rows.append(
                    f"• {rule['label']}: {metric['score']:.1f}점, "
                    f"인구 천 명당 {metric['per_1000']:.2f}개 "
                    f"(시설 수 순위점수 {metric['count_points']:.1f}, "
                    f"천 명당 순위점수 {metric['density_points']:.1f})."
                )
    if any(word in question for word in ("추천", "순위", "높은", "많은", "가장")):
        selected = ", ".join(facts["selected_categories"])
        rows.append(
            f"{selected} 공급점수 평균 상위 후보 (거주 적합도 순위가 아닙니다):"
        )
        rows.extend(
            f"• {r['label']}: 선택 부문 {r['selected_category_score']:.1f}점, "
            f"종합 {r['score']:.1f}점"
            for r in facts["candidates"]
        )
    if len(facts["regions"]) == 2:
        a, b = facts["regions"]
        rows.append(
            f"두 지역의 종합 공급점수 차이: {abs(a['score'] - b['score']):.1f}점."
        )
    for preview in facts["place_previews"]:
        rows.append(
            f"시설 목록: 전체 {preview['total']:,}개 중 이름순 최대 5개 (인기 순위 아님)."
        )
        rows.extend(
            f"• {p['name']} {p['branch_name'] or ''} — {p['address']}"
            for p in preview["items"]
        )
    if any(
        word in question
        for word in (
            "아이",
            "영유아",
            "자녀",
            "학군",
            "산책",
            "안전",
            "집값",
            "30대",
            "60대",
        )
    ):
        rows.append(
            "연령별 맞춤 가중치는 검증되지 않았습니다. 소아과·학군·산책로·안전·집값은 "
            "현재 자료로 판단할 수 없으며, 병의원 수에는 진료과 구분이 없습니다."
        )
    rows.append(facts["metadata"]["limitation"])
    rows.append(
        "기준: 상가 2026-06 / 인구 2026-08 · " + facts["metadata"]["score_version"]
    )
    return "\n\n".join(rows)


def answer_question(
    snapshot: dict,
    question: str,
    region_ids: list[str],
    db_path=None,
    chat_history: list[dict[str, Any]] | None = None,
) -> dict:
    facts = build_chat_facts(snapshot, question, region_ids, db_path)
    fallback_region_id, fallback_service_groups = resolve_chat_context(
        snapshot,
        question,
        region_ids,
        chat_history or [],
    )
    db_first = build_db_first_fact_answer(
        question,
        fallback_region_id=fallback_region_id,
        fallback_service_groups=fallback_service_groups,
    )
    if db_first:
        answer, structured_fact_pack = db_first
        structured_region_ids = [
            region["region_id"]
            for region in structured_fact_pack.get("ranked_region_candidates", [])
        ]
        structured_region_ids = structured_region_ids or [
            region_fact["region"]["region_id"]
            for region_fact in structured_fact_pack.get("region_facts", [])
        ]
        facts["structured_fact_pack"] = structured_fact_pack
    else:
        answer = database_answer(facts, question)
        structured_region_ids = []
        structured_fact_pack = {}

    mode, note = "database", "프로젝트 DB에서 계산한 응답"
    return {
        "answer": answer,
        "mode": mode,
        "note": note,
        "evidence": answer if db_first else database_answer(facts, question),
        "region_ids": structured_region_ids or [r["region_id"] for r in facts["regions"]],
        "query_context": {
            "region_ids": structured_region_ids or [r["region_id"] for r in facts["regions"]],
            "service_groups": structured_fact_pack.get("parsed", {}).get(
                "service_groups",
                [],
            ),
        },
        "snapshot_id": snapshot["metadata"]["snapshot_id"],
    }


def build_db_first_fact_answer(
    question: str,
    fallback_region_id: str | None = None,
    fallback_service_groups: list[str] | None = None,
) -> tuple[str, dict] | None:
    fact_pack = build_question_fact_pack(
        question,
        fallback_region_id=fallback_region_id,
        fallback_service_groups=fallback_service_groups,
    )
    if fact_pack["intent"] == "rank_regions" and fact_pack.get(
        "ranked_region_candidates"
    ):
        return build_template_answer(fact_pack), fact_pack
    if fact_pack["intent"] in {
        "place_candidates",
        "count_places",
        "list_places",
    } and fact_pack.get("region_facts"):
        return build_template_answer(fact_pack), fact_pack
    for region_fact in fact_pack.get("region_facts", []):
        if region_fact.get("selected_demographic"):
            return build_template_answer(fact_pack), fact_pack
    if not fact_pack.get("ranked_region_candidates"):
        return None
    return build_template_answer(fact_pack), fact_pack


def resolve_chat_context(
    snapshot: dict,
    question: str,
    region_ids: list[str],
    chat_history: list[dict[str, Any]],
) -> tuple[str | None, list[str] | None]:
    valid_region_ids = {region["region_id"] for region in snapshot["regions"]}
    structured_query = structure_question(question)
    current_regions = structured_query.region_labels
    current_services = structured_query.service_groups

    fallback_region_id = region_ids[0] if region_ids else None
    fallback_service_groups = None

    for turn in reversed(chat_history):
        history_region_ids = [
            region_id
            for region_id in turn.get("region_ids", [])
            if region_id in valid_region_ids
        ]
        history_service_groups = [
            service_group
            for service_group in turn.get("service_groups", [])
            if isinstance(service_group, str)
        ]
        if not current_regions and history_region_ids:
            fallback_region_id = history_region_ids[0]
        if not current_services and history_service_groups and fallback_service_groups is None:
            fallback_service_groups = history_service_groups
        if (
            (current_regions or fallback_region_id)
            and (current_services or fallback_service_groups)
        ):
            break

    return fallback_region_id, fallback_service_groups
