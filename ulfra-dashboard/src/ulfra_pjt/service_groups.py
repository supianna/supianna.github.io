from __future__ import annotations

SERVICE_GROUPS: dict[str, dict[str, list[str]]] = {
    "병의원": {"sub_group": ["병원", "의원"]},
    "치과": {"category_id": ["Q10210"]},
    "카페": {"category_id": ["I21201"]},
    "편의점": {"category_id": ["G20405"]},
    "슈퍼마켓": {"category_id": ["G20404"]},
    "한식": {"sub_group": ["한식"]},
    "중식": {"sub_group": ["중식"]},
    "일식": {"sub_group": ["일식"]},
    "양식": {"sub_group": ["서양식"]},
    "분식": {"category_id": ["I21007"]},
    "주점": {"sub_group": ["주점"]},
    "헬스장": {"category_id": ["R10307"]},
    "PC방": {"category_id": ["R10406"]},
}


def get_service_group_names() -> list[str]:
    """UI에 표시할 서비스 그룹 이름을 정의 순서대로 반환합니다."""
    return list(SERVICE_GROUPS.keys())


def validate_service_groups(service_groups: list[str] | None) -> list[str]:
    """알 수 없는 서비스 그룹 이름이 들어오면 명확한 오류를 냅니다."""
    if not service_groups:
        return []

    unknown_groups = [name for name in service_groups if name not in SERVICE_GROUPS]
    if unknown_groups:
        valid_names = ", ".join(get_service_group_names())
        unknown_names = ", ".join(unknown_groups)
        raise ValueError(f"알 수 없는 서비스 그룹입니다: {unknown_names}. 사용 가능: {valid_names}")

    return service_groups
