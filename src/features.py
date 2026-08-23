from . import config, etl

USER_FEATURES = config.DATA_PROCESSED / "user_features.parquet"


def build() -> None:
    if not config.CLEAN_PARQUET.exists():
        etl.clean()

    con = etl.connect()
    p = config.CLEAN_PARQUET.as_posix()
    con.execute(
        f"""
        COPY (
            SELECT
                user_id,
                MAX(CASE WHEN behavior_type = 'pv' THEN 1 ELSE 0 END) AS has_pv,
                MAX(CASE WHEN behavior_type = 'cart' THEN 1 ELSE 0 END) AS has_cart,
                MAX(CASE WHEN behavior_type = 'fav' THEN 1 ELSE 0 END) AS has_fav,
                MAX(CASE WHEN behavior_type = 'buy' THEN 1 ELSE 0 END) AS has_buy,
                SUM(CASE WHEN behavior_type = 'pv' THEN 1 ELSE 0 END) AS pv_cnt,
                SUM(CASE WHEN behavior_type = 'cart' THEN 1 ELSE 0 END) AS cart_cnt,
                SUM(CASE WHEN behavior_type = 'fav' THEN 1 ELSE 0 END) AS fav_cnt,
                SUM(CASE WHEN behavior_type = 'buy' THEN 1 ELSE 0 END) AS buy_cnt,
                COUNT(*) AS total_cnt,
                MIN(event_time) AS first_time,
                MAX(event_time) AS last_time
            FROM read_parquet('{p}')
            GROUP BY user_id
        ) TO '{USER_FEATURES.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    n = con.execute(
        f"SELECT count(*) FROM read_parquet('{USER_FEATURES.as_posix()}')"
    ).fetchone()[0]
    print(f"[features] 用户特征表已生成：{n} 用户 -> {USER_FEATURES.as_posix()}")
    con.close()
