-- 漏斗分析 SQL（基于清洗后 parquet，DuckDB 语法）
-- 数据：data/processed/user_behavior_clean.parquet
-- 口径说明：
--   事件级 = 按行为次数计数；用户级 = 按去重 user_id 计数

-- ============ 1. 事件级漏斗（行为次数） ============
SELECT
    count(*) FILTER (WHERE behavior_type = 'pv')   AS pv_events,
    count(*) FILTER (WHERE behavior_type = 'cart') AS cart_events,
    count(*) FILTER (WHERE behavior_type = 'fav')  AS fav_events,
    count(*) FILTER (WHERE behavior_type = 'buy')  AS buy_events
FROM read_parquet('data/processed/user_behavior_clean.parquet');

-- ============ 2. 用户级漏斗（去重用户） ============
WITH ub AS (
    SELECT
        user_id,
        MAX(CASE WHEN behavior_type = 'pv' THEN 1 ELSE 0 END)   AS has_pv,
        MAX(CASE WHEN behavior_type = 'cart' THEN 1 ELSE 0 END) AS has_cart,
        MAX(CASE WHEN behavior_type = 'fav' THEN 1 ELSE 0 END)  AS has_fav,
        MAX(CASE WHEN behavior_type = 'buy' THEN 1 ELSE 0 END)  AS has_buy
    FROM read_parquet('data/processed/user_behavior_clean.parquet')
    GROUP BY user_id
)
SELECT
    count(*) FILTER (WHERE has_pv = 1)                                AS pv_users,
    count(*) FILTER (WHERE has_cart = 1)                              AS cart_users,
    count(*) FILTER (WHERE has_fav = 1)                               AS fav_users,
    count(*) FILTER (WHERE has_buy = 1)                               AS buy_users,
    count(*) FILTER (WHERE has_pv = 1 AND has_cart = 1)               AS pv_cart_users,
    count(*) FILTER (WHERE has_pv = 1 AND has_buy = 1)                AS pv_buy_users,
    count(*) FILTER (WHERE has_cart = 1 AND has_buy = 1)              AS cart_buy_users,
    count(*) FILTER (WHERE has_fav = 1 AND has_buy = 1)               AS fav_buy_users
FROM ub;

-- ============ 3. 按日漏斗（每日去重用户） ============
SELECT
    event_date AS date,
    count(DISTINCT user_id) FILTER (WHERE behavior_type = 'pv')   AS pv_users,
    count(DISTINCT user_id) FILTER (WHERE behavior_type = 'cart') AS cart_users,
    count(DISTINCT user_id) FILTER (WHERE behavior_type = 'fav')  AS fav_users,
    count(DISTINCT user_id) FILTER (WHERE behavior_type = 'buy')  AS buy_users
FROM read_parquet('data/processed/user_behavior_clean.parquet')
GROUP BY event_date
ORDER BY event_date;

-- ============ 4. TOP 类目漏斗（按购买用户数排序） ============
WITH cat AS (
    SELECT
        category_id,
        count(DISTINCT user_id) FILTER (WHERE behavior_type = 'pv')   AS pv_users,
        count(DISTINCT user_id) FILTER (WHERE behavior_type = 'cart') AS cart_users,
        count(DISTINCT user_id) FILTER (WHERE behavior_type = 'fav')  AS fav_users,
        count(DISTINCT user_id) FILTER (WHERE behavior_type = 'buy')  AS buy_users
    FROM read_parquet('data/processed/user_behavior_clean.parquet')
    GROUP BY category_id
)
SELECT *
FROM cat
ORDER BY buy_users DESC
LIMIT 10;

-- ============ 5. 小时分布（各行为热度） ============
SELECT
    hour,
    count(*) FILTER (WHERE behavior_type = 'pv')   AS pv,
    count(*) FILTER (WHERE behavior_type = 'cart') AS cart,
    count(*) FILTER (WHERE behavior_type = 'fav')  AS fav,
    count(*) FILTER (WHERE behavior_type = 'buy')  AS buy
FROM read_parquet('data/processed/user_behavior_clean.parquet')
GROUP BY hour
ORDER BY hour;
