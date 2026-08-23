from __future__ import annotations

import pandas as pd

from . import config, etl, features

REFERENCE_TIME = pd.Timestamp("2017-12-03 23:59:59")

SEGMENT_LABELS = {
    # (R高, F高, M高) -> 客户类型
    (1, 1, 1): "重要价值客户",
    (1, 1, 0): "一般价值客户",
    (1, 0, 1): "重要发展客户",
    (1, 0, 0): "一般发展客户",
    (0, 1, 1): "重要保持客户",
    (0, 1, 0): "一般保持客户",
    (0, 0, 1): "重要挽留客户",
    (0, 0, 0): "一般挽留客户",
}


def load() -> pd.DataFrame:
    con = etl.connect()
    df = con.execute(
        f"""
        SELECT
            user_id,
            has_pv, has_cart, has_fav, has_buy,
            pv_cnt, cart_cnt, fav_cnt, buy_cnt,
            date_diff('day', last_time, TIMESTAMPTZ '2017-12-03 23:59:59+08:00') AS recency_days,
            total_cnt AS frequency,
            buy_cnt AS monetary
        FROM read_parquet('{features.USER_FEATURES.as_posix()}')
        """
    ).fetchdf()
    con.close()
    return df


def score(df: pd.DataFrame) -> pd.DataFrame:
    # 用 rank 消除并列值导致的 qcut 重复边界
    # R：越小越好（越近分数越高）
    df["r_score"] = pd.qcut(
        df["recency_days"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]
    )
    # F、M：越大越好
    df["f_score"] = pd.qcut(
        df["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
    )
    df["m_score"] = pd.qcut(
        df["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
    )
    for c in ("r_score", "f_score", "m_score"):
        df[c] = df[c].astype(int)
    return df


def segment(df: pd.DataFrame) -> pd.DataFrame:
    r_med = df["recency_days"].median()
    f_med = df["frequency"].median()
    m_med = df["monetary"].median()
    df["r_high"] = (df["recency_days"] <= r_med).astype(int)
    df["f_high"] = (df["frequency"] > f_med).astype(int)
    df["m_high"] = (df["monetary"] > m_med).astype(int)
    df["segment"] = df.apply(
        lambda r: SEGMENT_LABELS[(r["r_high"], r["f_high"], r["m_high"])],
        axis=1,
    )
    return df


def run() -> pd.DataFrame:
    df = load()
    df = score(df)
    df = segment(df)

    summary = (
        df.groupby("segment")
        .agg(
            users=("user_id", "count"),
            avg_recency_days=("recency_days", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
        )
        .reset_index()
    )
    summary["pct"] = (summary["users"] / summary["users"].sum() * 100).round(2)
    summary = summary.sort_values("users", ascending=False).reset_index(drop=True)

    # 保持固定展示顺序
    order = {k: i for i, k in enumerate(SEGMENT_LABELS.values())}
    summary["_o"] = summary["segment"].map(order)
    summary = summary.sort_values("_o").drop(columns="_o").reset_index(drop=True)
    summary["avg_recency_days"] = summary["avg_recency_days"].round(1)
    summary["avg_frequency"] = summary["avg_frequency"].round(1)
    summary["avg_monetary"] = summary["avg_monetary"].round(2)

    print("=== RFM 用户分群（8 类） ===")
    print(summary.to_string(index=False))
    print(
        f"\n中位数阈值：R(recency) <= {df['recency_days'].median()} 天、"
        f"F(frequency) > {df['frequency'].median()}、M(购买次数) > {df['monetary'].median()}"
    )
    return df, summary


def export() -> None:
    config.OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    df, summary = run()
    summary.to_csv(config.OUTPUT_TABLES / "rfm_segments.csv", index=False, encoding="utf-8-sig")

    score_dist = (
        df.groupby(["r_score", "f_score", "m_score"]).size().reset_index(name="users")
    )
    score_dist.to_csv(config.OUTPUT_TABLES / "rfm_score_distribution.csv", index=False, encoding="utf-8-sig")

    # 用户级明细（供 Tableau 钻取），仅保留关键列
    user_level = df[
        ["user_id", "recency_days", "frequency", "monetary",
         "r_score", "f_score", "m_score", "segment",
         "pv_cnt", "cart_cnt", "fav_cnt", "buy_cnt"]
    ]
    user_level.to_csv(config.OUTPUT_TABLES / "rfm_user_level.csv", index=False, encoding="utf-8-sig")
    print("\nRFM 分析结果已导出至 output/tables/")
