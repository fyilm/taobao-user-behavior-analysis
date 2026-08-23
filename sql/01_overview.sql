-- 数据探查：整体概览与质量检查
CREATE OR REPLACE VIEW u AS
SELECT *
FROM read_csv(
    'data/raw/UserBehavior.csv',
    header = false,
    columns = {
        'user_id': 'BIGINT',
        'item_id': 'BIGINT',
        'category_id': 'BIGINT',
        'behavior_type': 'VARCHAR',
        'ts': 'BIGINT'
    }
);

-- 1) 基本规模
SELECT
    count(*)                                        AS total_rows,
    count(DISTINCT user_id)                         AS users,
    count(DISTINCT item_id)                         AS items,
    count(DISTINCT category_id)                     AS categories,
    count(DISTINCT behavior_type)                   AS behavior_types,
    min(to_timestamp(ts))                           AS min_ts,
    max(to_timestamp(ts))                           AS max_ts
FROM u;

-- 2) 缺失值
SELECT
    count(*) FILTER (WHERE user_id IS NULL)         AS null_user,
    count(*) FILTER (WHERE item_id IS NULL)         AS null_item,
    count(*) FILTER (WHERE category_id IS NULL)     AS null_category,
    count(*) FILTER (WHERE behavior_type IS NULL)   AS null_behavior,
    count(*) FILTER (WHERE ts IS NULL)              AS null_ts
FROM u;

-- 3) 非法行为类型
SELECT behavior_type, count(*) AS cnt
FROM u
WHERE behavior_type NOT IN ('pv', 'buy', 'cart', 'fav')
GROUP BY behavior_type;

-- 4) 行为类型分布
SELECT behavior_type, count(*) AS cnt
FROM u
GROUP BY behavior_type
ORDER BY cnt DESC;

-- 5) 完全重复行
SELECT count(*) AS dup_rows
FROM (SELECT user_id, item_id, category_id, behavior_type, ts
      FROM u
      GROUP BY 1, 2, 3, 4, 5
      HAVING count(*) > 1);
