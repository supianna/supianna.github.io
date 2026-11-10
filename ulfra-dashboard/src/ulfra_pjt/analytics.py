from __future__ import annotations

from typing import Any

import pandas as pd

from ulfra_pjt.queries import compare_regions, get_region, get_region_service_counts

AGE_COLUMNS = {
    "0~9세": "pop_0s",
    "10~19세": "pop_10s",
    "20~29세": "pop_20s",
    "30~49세": "pop_3040s",
    "50~69세": "pop_5060s",
    "70세 이상": "pop_70over",
}

GENDER_COLUMNS = {
    "남성": "male_pop",
    "여성": "female_pop",
}


def _ratio(value: float, total: float) -> float:
    return float(value) / float(total) * 100 if total else 0.0


def calculate_age_distribution(region: dict[str, Any]) -> pd.DataFrame:
    """단일 지역의 연령대별 인구와 구성비를 반환합니다."""
    total_pop = int(region["total_pop"])
    rows = []

    for order, (age_group, column_name) in enumerate(AGE_COLUMNS.items(), start=1):
        population = int(region[column_name])
        rows.append(
            {
                "age_group": age_group,
                "population": population,
                "ratio": _ratio(population, total_pop),
                "sort_order": order,
            }
        )

    return pd.DataFrame(rows)


def calculate_gender_distribution(region: dict[str, Any]) -> pd.DataFrame:
    """단일 지역의 성별 인구와 구성비를 반환합니다."""
    total_pop = int(region["total_pop"])
    rows = []

    for gender, column_name in GENDER_COLUMNS.items():
        population = int(region[column_name])
        rows.append(
            {
                "gender": gender,
                "population": population,
                "ratio": _ratio(population, total_pop),
            }
        )

    return pd.DataFrame(rows)


def calculate_service_density(
    region: dict[str, Any],
    service_counts: pd.DataFrame,
) -> pd.DataFrame:
    """서비스 그룹별 시설 수와 인구 1,000명당 시설 수를 반환합니다."""
    total_pop = int(region["total_pop"])
    density = service_counts.copy()
    density["total_pop"] = total_pop
    density["places_per_1000"] = density["place_count"].apply(
        lambda count: float(count) / total_pop * 1000 if total_pop else 0.0
    )
    return density


def build_region_analysis(region_id: str) -> dict[str, pd.DataFrame | dict[str, Any]]:
    """지역 상세 화면에서 바로 사용할 분석 묶음을 반환합니다."""
    region = get_region(region_id)
    if region is None:
        raise ValueError(f"존재하지 않는 region_id입니다: {region_id}")

    service_counts = get_region_service_counts(region_id)

    return {
        "region": region,
        "age_distribution": calculate_age_distribution(region),
        "gender_distribution": calculate_gender_distribution(region),
        "service_counts": service_counts,
        "service_density": calculate_service_density(region, service_counts),
    }


def build_region_comparison(region_ids: list[str]) -> pd.DataFrame:
    """두 개 이상 지역 비교에 사용할 long-form DataFrame을 반환합니다."""
    comparison = compare_regions(region_ids).copy()
    if comparison.empty:
        return comparison

    comparison["region_label"] = (
        comparison["gu_name"] + " " + comparison["dong_name"]
    )
    return comparison[
        [
            "region_id",
            "region_label",
            "gu_name",
            "dong_name",
            "total_pop",
            "service_group",
            "place_count",
            "places_per_1000",
        ]
    ]
