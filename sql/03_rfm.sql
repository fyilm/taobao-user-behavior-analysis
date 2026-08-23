-- RFM 特征聚合 SQL（基于清洗后 parquet，DuckDB 语法）
-- 生成「用户特征表」data/processed/user_features.parquet
-- R = 距末次行为天数（基准 2017-12-03 23:59:59）
-- F = 行为总次数（活跃频率）
-- M = 购买次数（本数据集无金额字段，以购买次数作为消费力代理）

COPY (
    SELECT
        user_id,
        MAX(CASE WHEN behavior_type = 'pv' THEN 1 ELSE 0 END)   AS has_pv,
        MAX(CASE WHEN behavior_type = 'cart' THEN 1 ELSE 0 END) AS has_cart,
        MAX(CASE WHEN behavior_type = 'fav' THEN 1 ELSE 0 END)  AS has_fav,
        MAX(CASE WHEN behavior_type = 'buy' THEN 1 ELSE 0 END)  AS has_buy,
        SUM(CASE WHEN behavior_type = 'pv' THEN 1 ELSE 0 END)   AS pv_cnt,
        SUM(CASE WHEN behavior_type = 'cart' THEN 1 ELSE 0 END) AS cart_cnt,
        SUM(CASE WHEN behavior_type = 'fav' THEN 1 ELSE 0 END)  AS fav_cnt,
        SUM(CASE WHEN behavior_type = 'buy' THEN 1 ELSE 0 END)  AS buy_cnt,
        COUNT(*)          AS total_cnt,          -- F
        MIN(event_time)   AS first_time,
        MAX(event_time)   AS last_time           -- 用于 R
    FROM read_parquet('data/processed/user_behavior_clean.parquet')
    GROUP BY user_id
) TO 'data/processed/user_features.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);

-- R 值计算（距末次行为天数）
SELECT
    user_id,
    date_diff('day', last_time, TIMESTAMPTZ '2017-12-03 23:59:59+08:00') AS recency_days,
    total_cnt AS frequency,
    buy_cnt   AS monetary
FROM read_parquet('data/processed/user_features.parquet');
