import tempfile

import duckdb

from . import config

RAW_PARQUET = config.DATA_PROCESSED / "user_behavior_raw.parquet"


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(f"SET temp_directory = '{tempfile.gettempdir()}'")
    return con


def _csv_columns() -> str:
    return (
        "{'user_id': 'BIGINT', 'item_id': 'BIGINT', 'category_id': 'BIGINT', "
        "'behavior_type': 'VARCHAR', 'ts': 'BIGINT'}"
    )


def to_parquet() -> None:
    """单次扫描：CSV -> 原始 parquet（不做过滤，保留原始事实）。"""
    con = connect()
    con.execute(
        f"""
        COPY (
            SELECT
                user_id,
                item_id,
                category_id,
                behavior_type,
                to_timestamp(ts) AS event_time
            FROM read_csv(
                '{config.RAW_CSV.as_posix()}',
                header = false,
                columns = {_csv_columns()}
            )
        ) TO '{RAW_PARQUET.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    n = con.execute(
        f"SELECT count(*) FROM read_parquet('{RAW_PARQUET.as_posix()}')"
    ).fetchone()[0]
    print(f"[to_parquet] 完成，共 {n} 行 -> {RAW_PARQUET.as_posix()}")
    con.close()


def run_overview() -> None:
    if not RAW_PARQUET.exists():
        to_parquet()

    con = connect()
    p = RAW_PARQUET.as_posix()
    print("=== 基本规模 ===")
    print(
        con.execute(
            f"""
            SELECT
                count(*) AS total_rows,
                count(DISTINCT user_id) AS users,
                count(DISTINCT item_id) AS items,
                count(DISTINCT category_id) AS categories,
                min(event_time) AS min_ts,
                max(event_time) AS max_ts
            FROM read_parquet('{p}')
            """
        ).fetchdf().to_string(index=False)
    )

    print("\n=== 缺失值 ===")
    print(
        con.execute(
            f"""
            SELECT
                count(*) FILTER (WHERE user_id IS NULL) AS null_user,
                count(*) FILTER (WHERE item_id IS NULL) AS null_item,
                count(*) FILTER (WHERE category_id IS NULL) AS null_category,
                count(*) FILTER (WHERE behavior_type IS NULL) AS null_behavior,
                count(*) FILTER (WHERE event_time IS NULL) AS null_ts
            FROM read_parquet('{p}')
            """
        ).fetchdf().to_string(index=False)
    )

    print("\n=== 行为类型分布 ===")
    print(
        con.execute(
            f"""
            SELECT behavior_type, count(*) AS cnt
            FROM read_parquet('{p}') GROUP BY 1 ORDER BY cnt DESC
            """
        ).fetchdf().to_string(index=False)
    )

    print("\n=== 非法行为类型 ===")
    print(
        con.execute(
            f"""
            SELECT behavior_type, count(*) AS cnt
            FROM read_parquet('{p}')
            WHERE behavior_type NOT IN ('pv', 'buy', 'cart', 'fav')
            GROUP BY 1
            """
        ).fetchdf().to_string(index=False)
    )

    print("\n=== 完全重复行 ===")
    print(
        con.execute(
            f"""
            SELECT count(*) AS dup_rows
            FROM (
                SELECT user_id, item_id, category_id, behavior_type, event_time
                FROM read_parquet('{p}')
                GROUP BY 1, 2, 3, 4, 5
                HAVING count(*) > 1
            )
            """
        ).fetchdf().to_string(index=False)
    )

    con.close()


def clean() -> None:
    if not RAW_PARQUET.exists():
        to_parquet()

    con = connect()
    p = RAW_PARQUET.as_posix()
    con.execute(
        f"""
        COPY (
            SELECT
                user_id,
                item_id,
                category_id,
                behavior_type,
                event_time,
                event_time::DATE AS event_date,
                date_part('hour', event_time) AS hour,
                date_part('dow', event_time) AS dow,
                date_part('year', event_time) * 10000
                    + date_part('month', event_time) * 100
                    + date_part('day', event_time) AS ymd
            FROM read_parquet('{p}')
            WHERE behavior_type IN ('pv', 'buy', 'cart', 'fav')
              AND user_id IS NOT NULL
              AND item_id IS NOT NULL
              AND category_id IS NOT NULL
              AND event_time >= TIMESTAMP '2017-11-25 00:00:00'
              AND event_time < TIMESTAMP '2017-12-04 00:00:00'
        ) TO '{config.CLEAN_PARQUET.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    stats = con.execute(
        f"""
        SELECT count(*) AS rows, count(DISTINCT user_id) AS users,
               count(DISTINCT item_id) AS items, count(DISTINCT category_id) AS cats
        FROM read_parquet('{config.CLEAN_PARQUET.as_posix()}')
        """
    ).fetchdf()
    print("=== 清洗后 parquet (9 天窗口 2017-11-25 ~ 12-03) ===")
    print(stats.to_string(index=False))
    con.close()
