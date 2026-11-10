"""포트폴리오용 대시보드의 로컬 SQLite 경로."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "Data" / "ulsan_infra.db"


def get_database_path(db_path: str | Path | None = None) -> Path:
    """프로젝트에 포함된 DB 또는 명시적으로 지정한 로컬 DB를 반환합니다."""
    path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"SQLite DB 파일을 찾을 수 없습니다: {path}")
    return path
