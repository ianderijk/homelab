from collections.abc import Mapping, Sequence
from contextvars import ContextVar
from os import getenv
from typing import Any, Literal

import polars as pl
from sqlalchemy import Engine, Row, Table, create_engine, insert, text

engine: ContextVar[Any] = ContextVar("engine", default=None)


def _create_engine() -> Engine | None:
    url = getenv("POSTGRES_URL")
    if url:
        return create_engine(str(url))


def get_engine() -> Engine:
    if engine.get() is None:
        engine.set(_create_engine())
    return engine.get()


def execute_statement(
    statement: str, params: Mapping[str, Any] = {}, engine: Engine | None = None
) -> None:
    """Function to allow execution of statements that do not return any results
    such as create and insert"""
    if engine is None:
        engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text(statement), params)
        conn.commit()


def execute_query(
    query: str, params: Mapping[str, Any] = {}, engine: Engine | None = None
) -> Sequence[Row[Any]]:
    """Funciton to allow execution of queries that return results"""
    if engine is None:
        engine = get_engine()
    with engine.connect() as conn:
        data = conn.execute(text(query), params)
        return data.fetchall()


def execute_bulk_insert(
    table: Table, values: list[dict[str, Any]], engine: Engine | None = None
) -> None:
    if engine is None:
        engine = get_engine()
    with engine.begin() as conn:
        conn.execute(insert(table), values)


def write_dataframe(
    df: pl.DataFrame,
    table: Table | str,
    if_table_exists: Literal["fail", "replace", "append"] = "append",
    engine: Engine | None = None,
) -> None:
    """Write a Polars DataFrame directly to a Postgres table."""
    if engine is None:
        engine = get_engine()

    table_name = table.name if isinstance(table, Table) else table

    df.write_database(
        table_name=table_name,
        connection=engine,
        if_table_exists=if_table_exists,
        engine="sqlalchemy",
    )
