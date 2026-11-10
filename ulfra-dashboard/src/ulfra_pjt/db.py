from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from ulfra_pjt.config import get_database_path

QueryParams = Sequence[Any] | dict[str, Any] | None


def connect_db(db_path: str | Path | None = None) -> sqlite3.Connection:
    """프로젝트에 포함된 SQLite 데이터베이스를 읽기 전용으로 엽니다."""
    path = get_database_path(db_path)
    uri = f"{path.as_uri()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def read_dataframe(
    sql: str,
    params: QueryParams = None,
    db_path: str | Path | None = None,
) -> pd.DataFrame:
    """파라미터 바인딩을 사용해 SQL 결과를 DataFrame으로 반환합니다."""
    with connect_db(db_path) as connection:
        return pd.read_sql_query(sql, connection, params=params)


def read_records(
    sql: str,
    params: QueryParams = None,
    db_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """파라미터 바인딩을 사용해 SQL 결과를 dict 목록으로 반환합니다."""
    with connect_db(db_path) as connection:
        cursor = connection.execute(sql, params or [])
        return [dict(row) for row in cursor.fetchall()]


def read_one(
    sql: str,
    params: QueryParams = None,
    db_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """파라미터 바인딩을 사용해 SQL 결과 한 행을 dict로 반환합니다."""
    with connect_db(db_path) as connection:
        cursor = connection.execute(sql, params or [])
        row = cursor.fetchone()
        return dict(row) if row else None
