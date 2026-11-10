"""HTML 대시보드의 공통 데이터 계약. SQLite는 항상 읽기 전용입니다."""

from contextlib import closing
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from time import perf_counter

from ulfra_pjt.config import get_database_path
from ulfra_pjt.db import connect_db
from ulfra_pjt.scoring import (
    CATEGORIES,
    SCORE_LIMITATION,
    SCORE_VERSION,
    calculate_scores,
)

VALID_COORDINATES = "p.latitude BETWEEN 32 AND 40 AND p.longitude BETWEEN 124 AND 132"


@lru_cache(maxsize=2)
def _snapshot(source: str, modified_ns: int, size: int) -> dict:
    started = perf_counter()
    category_sql = ", ".join(
        f"SUM(CASE WHEN {rule['condition']} THEN 1 ELSE 0 END) AS {key}"
        for key, rule in CATEGORIES.items()
    )
    # 한 연결의 읽기 트랜잭션에서 인구·시설·품질 통계를 함께 읽습니다.
    with closing(connect_db(source)) as connection:
        connection.execute("BEGIN")
        observations = [
            dict(row)
            for row in connection.execute(f"""
            SELECT r.*, COUNT(p.place_id) AS total_places,
                AVG(CASE WHEN {VALID_COORDINATES} THEN p.latitude END) AS latitude,
                AVG(CASE WHEN {VALID_COORDINATES} THEN p.longitude END) AS longitude,
                SUM(CASE WHEN c.sub_name LIKE '%학원%' THEN 1 ELSE 0 END) AS academy_places,
                SUM(CASE WHEN c.sub_group = '의원' THEN 1 ELSE 0 END) AS clinic_places,
                {category_sql}
            FROM regions r LEFT JOIN places p ON r.region_id = p.region_id
            LEFT JOIN categories c ON p.category_id = c.category_id
            GROUP BY r.region_id ORDER BY r.gu_name, r.dong_name
        """)
        ]
        quality = dict(
            connection.execute(f"""
            SELECT COUNT(*) AS total_places,
                SUM(CASE WHEN {VALID_COORDINATES} THEN 1 ELSE 0 END) AS valid_coordinates,
                SUM(CASE WHEN r.region_id IS NULL THEN 1 ELSE 0 END) AS unmapped_regions,
                SUM(CASE WHEN c.category_id IS NULL THEN 1 ELSE 0 END) AS unmapped_categories
            FROM places p LEFT JOIN regions r ON p.region_id = r.region_id
            LEFT JOIN categories c ON p.category_id = c.category_id
        """).fetchone()
        )
    if quality["unmapped_regions"] or quality["unmapped_categories"]:
        raise ValueError("시설의 지역/업종 연결이 누락되어 점수 산출을 보류합니다.")
    regions = calculate_scores(observations)
    return {
        "metadata": {
            "score_version": SCORE_VERSION,
            "score_name": "생활인프라 공급점수",
            "reference_scope": "울산 전체 읍면동 고정 기준",
            "region_count": len(regions),
            "district_count": len({r["gu_name"] for r in regions}),
            "total_population": sum(r["total_pop"] for r in regions),
            "source": "프로젝트 SQLite / 소상공인 상가정보 + 행정동 인구",
            "commercial_reference": "2026-06",
            "population_reference": "2026-08",
            "reference_note": "프로젝트 제공 원천자료 기준월. 실시간 영업·인구 자료가 아닙니다.",
            "snapshot_id": f"{SCORE_VERSION}-{modified_ns}-{size}",
            "loaded_at": datetime.now(UTC).isoformat(),
            "query_ms": round((perf_counter() - started) * 1000, 2),
            "formula": "평균[0.5 × 시설 수 평균순위점수 + 0.5 × 인구 천 명당 시설 수 평균순위점수]",
            "limitation": SCORE_LIMITATION,
            "map_note": "동네 표시는 유효한 시설 좌표의 평균 위치이며 행정동 경계나 공식 중심점이 아닙니다.",
            "quality_note": "좌표 채움/범위 검사는 위치 정확도 또는 실제 영업 여부 검증이 아닙니다.",
        },
        "categories": {
            key: {"label": rule["label"]} for key, rule in CATEGORIES.items()
        },
        "quality": quality,
        "regions": regions,
    }


def get_snapshot(db_path: str | Path | None = None) -> dict:
    path = get_database_path(db_path)
    stat = path.stat()
    return _snapshot(str(path), stat.st_mtime_ns, stat.st_size)


def find_region(snapshot: dict, region_id: str) -> dict:
    for region in snapshot["regions"]:
        if region["region_id"] == region_id:
            return region
    raise KeyError(region_id)


def list_places(
    region_id: str,
    category: str = "all",
    offset: int = 0,
    limit: int = 100,
    db_path: str | Path | None = None,
) -> dict:
    # 업종 조건은 허용목록에서만 선택하고 ID/페이지는 파라미터로 바인딩합니다.
    if category != "all" and category not in CATEGORIES:
        raise ValueError("지원하지 않는 업종입니다.")
    if offset < 0 or not 1 <= limit <= 500:
        raise ValueError("잘못된 페이지 범위입니다.")
    condition = "1=1" if category == "all" else CATEGORIES[category]["condition"]
    base_sql = f"""FROM places p JOIN categories c ON p.category_id = c.category_id
                   WHERE p.region_id = ? AND ({condition})"""
    with closing(connect_db(db_path)) as connection:
        connection.execute("BEGIN")
        total = connection.execute(
            f"SELECT COUNT(*) {base_sql}", [region_id]
        ).fetchone()[0]
        rows = [
            dict(row)
            for row in connection.execute(
                f"""
            SELECT p.place_id, p.name, p.branch_name, p.address, p.latitude, p.longitude,
                c.sub_name, c.sub_group,
                CASE WHEN {VALID_COORDINATES} THEN 1 ELSE 0 END AS coordinate_valid
            {base_sql} ORDER BY p.name, p.place_id LIMIT ? OFFSET ?
        """,
                [region_id, limit, offset],
            )
        ]
    next_offset = offset + len(rows) if offset + len(rows) < total else None
    return {
        "region_id": region_id,
        "category": category,
        "total": total,
        "offset": offset,
        "limit": limit,
        "next_offset": next_offset,
        "items": rows,
    }


def search_places(
    query: str,
    district: str | None = None,
    region_id: str | None = None,
    limit: int = 100,
    db_path: str | Path | None = None,
) -> dict:
    conditions = [VALID_COORDINATES, "instr(lower(p.name), lower(?)) > 0"]
    params = [query.strip()]
    if region_id:
        conditions.append("p.region_id = ?")
        params.append(region_id)
    elif district:
        conditions.append("r.gu_name = ?")
        params.append(district)
    source = f"FROM places p JOIN regions r ON p.region_id = r.region_id WHERE {' AND '.join(conditions)}"
    with closing(connect_db(db_path)) as connection:
        total = connection.execute(f"SELECT COUNT(*) {source}", params).fetchone()[0]
        items = [dict(row) for row in connection.execute(
            f"""SELECT p.place_id, p.name, p.address, p.latitude, p.longitude,
                       r.gu_name, r.dong_name {source}
                ORDER BY p.name, p.place_id LIMIT ?""",
            [*params, limit],
        )]
    return {"total": total, "items": items}


def compare(snapshot: dict, region_a: str, region_b: str) -> dict:
    a, b = find_region(snapshot, region_a), find_region(snapshot, region_b)
    differences = {
        key: a["categories"][key]["score"] - b["categories"][key]["score"]
        for key in CATEGORIES
    }
    label_a, label_b = (
        f"{a['gu_name']} {a['dong_name']}",
        f"{b['gu_name']} {b['dong_name']}",
    )
    summary = (
        f"{label_a} {a['score']:.1f}점({a['rank']}위), "
        f"{label_b} {b['score']:.1f}점({b['rank']}위). "
        f"점수 차이는 {abs(a['score'] - b['score']):.1f}점입니다."
    )
    return {
        "a": a,
        "b": b,
        "differences": differences,
        "summary": summary,
        "metadata": snapshot["metadata"],
    }
