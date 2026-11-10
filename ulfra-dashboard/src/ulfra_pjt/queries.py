from __future__ import annotations

from typing import Any

import pandas as pd

from ulfra_pjt.db import read_dataframe, read_one
from ulfra_pjt.service_groups import SERVICE_GROUPS, validate_service_groups

PLACE_COLUMNS = """
    p.place_id,
    p.name,
    p.branch_name,
    p.address,
    p.latitude,
    p.longitude,
    p.region_id,
    r.gu_name,
    r.dong_name,
    p.category_id,
    c.main_group,
    c.sub_group,
    c.sub_name
"""


def _placeholders(values: list[Any]) -> str:
    return ", ".join("?" for _ in values)


def _build_service_group_filter(service_groups: list[str] | None) -> tuple[str, list[Any]]:
    selected_groups = validate_service_groups(service_groups)
    if not selected_groups:
        return "", []

    conditions: list[str] = []
    params: list[Any] = []

    for group_name in selected_groups:
        rule = SERVICE_GROUPS[group_name]

        if "category_id" in rule:
            values = rule["category_id"]
            conditions.append(f"c.category_id IN ({_placeholders(values)})")
            params.extend(values)

        if "sub_group" in rule:
            values = rule["sub_group"]
            conditions.append(f"c.sub_group IN ({_placeholders(values)})")
            params.extend(values)

    return f" AND ({' OR '.join(conditions)})", params


def _service_group_count_sql(group_name: str) -> tuple[str, list[Any]]:
    filter_sql, params = _build_service_group_filter([group_name])
    sql = f"""
        SELECT COUNT(*) AS place_count
        FROM places p
        JOIN categories c ON p.category_id = c.category_id
        WHERE p.region_id = ?
        {filter_sql}
    """
    return sql, params


def _safe_limit(limit: int, max_limit: int = 10_000) -> int:
    return max(1, min(int(limit), max_limit))


def _escape_like(keyword: str) -> str:
    return (
        keyword.strip()
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def get_gu_list() -> list[str]:
    """울산 구/군 목록을 가나다순으로 반환합니다."""
    records = read_dataframe(
        """
        SELECT DISTINCT gu_name
        FROM regions
        ORDER BY gu_name
        """
    )
    return records["gu_name"].tolist()


def get_regions(gu_name: str | None = None) -> pd.DataFrame:
    """구/군 조건에 맞는 행정동 목록을 반환합니다."""
    if gu_name:
        return read_dataframe(
            """
            SELECT region_id, gu_name, dong_name, total_pop
            FROM regions
            WHERE gu_name = ?
            ORDER BY dong_name
            """,
            [gu_name],
        )

    return read_dataframe(
        """
        SELECT region_id, gu_name, dong_name, total_pop
        FROM regions
        ORDER BY gu_name, dong_name
        """
    )


def get_region(region_id: str) -> dict[str, Any] | None:
    """행정동 코드로 단일 지역 정보를 반환합니다."""
    return read_one(
        """
        SELECT *
        FROM regions
        WHERE region_id = ?
        """,
        [region_id],
    )


def get_category_options() -> pd.DataFrame:
    """원천 카테고리 목록을 반환합니다."""
    return read_dataframe(
        """
        SELECT category_id, main_group, sub_group, sub_name
        FROM categories
        ORDER BY main_group, sub_group, sub_name
        """
    )


def get_places(
    region_id: str,
    service_groups: list[str] | None,
    limit: int = 5_000,
) -> pd.DataFrame:
    """지역과 서비스 그룹 조건에 맞는 장소 목록을 반환합니다."""
    filter_sql, filter_params = _build_service_group_filter(service_groups)
    safe_limit = _safe_limit(limit)

    return read_dataframe(
        f"""
        SELECT {PLACE_COLUMNS}
        FROM places p
        JOIN regions r ON p.region_id = r.region_id
        JOIN categories c ON p.category_id = c.category_id
        WHERE p.region_id = ?
        {filter_sql}
        ORDER BY p.name, p.place_id
        LIMIT ?
        """,
        [region_id, *filter_params, safe_limit],
    )


def get_places_by_category_ids(
    region_id: str,
    category_ids: list[str],
    limit: int = 5_000,
) -> pd.DataFrame:
    """지역과 원천 카테고리 ID 조건에 맞는 장소 목록을 반환합니다."""
    if not category_ids:
        return pd.DataFrame()

    safe_limit = _safe_limit(limit)
    category_filter = _placeholders(category_ids)

    return read_dataframe(
        f"""
        SELECT {PLACE_COLUMNS}
        FROM places p
        JOIN regions r ON p.region_id = r.region_id
        JOIN categories c ON p.category_id = c.category_id
        WHERE p.region_id = ?
        AND c.category_id IN ({category_filter})
        ORDER BY p.name, p.place_id
        LIMIT ?
        """,
        [region_id, *category_ids, safe_limit],
    )


def count_places_by_category_ids(region_id: str, category_ids: list[str]) -> int:
    """지역과 원천 카테고리 ID 조건에 맞는 장소 수를 반환합니다."""
    if not category_ids:
        return 0

    category_filter = _placeholders(category_ids)
    record = read_one(
        f"""
        SELECT COUNT(*) AS place_count
        FROM places p
        WHERE p.region_id = ?
        AND p.category_id IN ({category_filter})
        """,
        [region_id, *category_ids],
    )
    return int(record["place_count"]) if record else 0


def get_region_service_counts(region_id: str) -> pd.DataFrame:
    """선택 지역의 서비스 그룹별 시설 수를 반환합니다."""
    rows: list[dict[str, Any]] = []

    for group_name in SERVICE_GROUPS:
        sql, params = _service_group_count_sql(group_name)
        record = read_one(sql, [region_id, *params])
        rows.append(
            {
                "region_id": region_id,
                "service_group": group_name,
                "place_count": int(record["place_count"]) if record else 0,
            }
        )

    return pd.DataFrame(rows)


def compare_regions(region_ids: list[str]) -> pd.DataFrame:
    """여러 지역의 인구와 서비스 그룹별 시설 수를 비교용 long-form DataFrame으로 반환합니다."""
    rows: list[dict[str, Any]] = []

    for region_id in region_ids:
        region = get_region(region_id)
        if not region:
            continue

        count_df = get_region_service_counts(region_id)
        total_pop = int(region["total_pop"])

        for _, count_row in count_df.iterrows():
            place_count = int(count_row["place_count"])
            per_1000 = place_count / total_pop * 1000 if total_pop else 0.0
            rows.append(
                {
                    "region_id": region_id,
                    "gu_name": region["gu_name"],
                    "dong_name": region["dong_name"],
                    "total_pop": total_pop,
                    "service_group": count_row["service_group"],
                    "place_count": place_count,
                    "places_per_1000": per_1000,
                }
            )

    return pd.DataFrame(rows)


def search_places(
    keyword: str,
    region_id: str | None = None,
    limit: int = 20,
) -> pd.DataFrame:
    """장소명, 지점명, 주소에서 키워드를 검색합니다."""
    clean_keyword = _escape_like(keyword)
    if not clean_keyword:
        return pd.DataFrame()

    safe_limit = _safe_limit(limit, max_limit=100)
    like_keyword = f"%{clean_keyword}%"
    params: list[Any] = [like_keyword, like_keyword, like_keyword]
    region_filter = ""

    if region_id:
        region_filter = "AND p.region_id = ?"
        params.append(region_id)

    params.append(safe_limit)

    return read_dataframe(
        f"""
        SELECT {PLACE_COLUMNS}
        FROM places p
        JOIN regions r ON p.region_id = r.region_id
        JOIN categories c ON p.category_id = c.category_id
        WHERE (
            p.name LIKE ? ESCAPE '\\'
            OR COALESCE(p.branch_name, '') LIKE ? ESCAPE '\\'
            OR p.address LIKE ? ESCAPE '\\'
        )
        {region_filter}
        ORDER BY p.name, p.place_id
        LIMIT ?
        """,
        params,
    )
