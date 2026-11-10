"""생활인프라 공급점수 v0.1: 원본을 바꾸지 않는 순수 계산 함수."""

from __future__ import annotations

import pandas as pd

SCORE_VERSION = "supply-v0.1"
# SQL 조건은 서버가 정의한 상수만 사용합니다. 사용자 입력을 SQL에 붙이지 않습니다.
CATEGORIES = {
    "medical": {
        "label": "병의원",
        "condition": "c.sub_group IN ('병원', '의원')",
    },
    "food": {
        "label": "식당",
        "condition": "c.main_group = '음식' AND c.sub_group IN "
        "('한식', '중식', '일식', '서양식', '동남아시아', '기타 간이')",
    },
    "cafe": {"label": "카페", "condition": "c.category_id = 'I21201'"},
    "shop": {
        "label": "쇼핑·생활소매",
        "condition": "c.main_group = '소매' AND c.sub_group IN "
        "('종합 소매', '식료품 소매', '섬유·의복·신발 소매', '기타 생활용품 소매')",
    },
}
SCORE_LIMITATION = (
    "울산 읍면동 간 상대적 시설 공급점수입니다. 시설 품질·접근시간·영업 여부·"
    "집값·치안·학교·공원·교통을 평가한 거주 적합도나 공인 지수가 아닙니다."
)


def rank_points(values: pd.Series) -> pd.Series:
    """동률은 평균 순위, 관측된 0은 0점, 모두 같은 양수는 50점입니다."""
    if values.isna().any() or (values < 0).any():
        raise ValueError("순위 계산에는 누락 없는 비음수 관측값이 필요합니다.")
    if values.nunique() == 1:
        return pd.Series(0.0 if values.iloc[0] == 0 else 50.0, index=values.index)
    points = 100 * (values.rank(method="average") - 1) / (len(values) - 1)
    return points.where(values != 0, 0.0)


def calculate_scores(observations: list[dict]) -> list[dict]:
    """전체 기준집단을 먼저 계산합니다. 지역 필터는 반환 이후에 적용합니다.

    인구나 카테고리 수집값이 누락되면 해당 동을 0점 처리하지 않습니다.
    기준집단이 바뀌는 것을 막기 위해 전체 점수 산출을 보류합니다.
    """
    if not observations:
        return []
    frame = pd.DataFrame(observations)
    columns = list(CATEGORIES)
    population = frame["total_pop"]
    if population.isna().any() or (population <= 0).any():
        raise ValueError("인구 누락 또는 0 이하 지역이 있어 점수를 산출할 수 없습니다.")
    if frame[columns].isna().any().any() or (frame[columns] < 0).any().any():
        raise ValueError(
            "카테고리 관측값 누락 또는 음수가 있어 점수를 산출할 수 없습니다."
        )

    category_results = {}
    for key in columns:
        counts = frame[key]
        density = counts / population * 1000
        count_points = rank_points(counts)
        density_points = rank_points(density)
        category_results[key] = {
            "count": counts,
            "per_1000": density,
            "count_points": count_points,
            "density_points": density_points,
            "score": (count_points + density_points) / 2,
        }
    totals = sum(category_results[key]["score"] for key in columns) / len(columns)
    ranks = totals.rank(method="min", ascending=False)
    results = []
    for index, observation in enumerate(observations):
        base = {key: value for key, value in observation.items() if key not in columns}
        base["categories"] = {
            key: {
                metric: int(values.iloc[index])
                if metric == "count"
                else float(values.iloc[index])
                for metric, values in metrics.items()
            }
            for key, metrics in category_results.items()
        }
        base.update(score=float(totals.iloc[index]), rank=int(ranks.iloc[index]))
        results.append(base)
    return results
