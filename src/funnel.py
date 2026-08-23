from __future__ import annotations

import pandas as pd

from . import config, etl, features


def _overall() -> pd.DataFrame:
    con = etl.connect()
    uf = features.USER_FEATURES.as_posix()
    row = con.execute(
        f"""
        SELECT
            count(*) FILTER (WHERE has_pv = 1)                                    AS pv,
            count(*) FILTER (WHERE has_cart = 1)                                  AS cart,
            count(*) FILTER (WHERE has_fav = 1)                                   AS fav,
            count(*) FILTER (WHERE has_buy = 1)                                   AS buy,
            count(*) FILTER (WHERE has_pv = 1 AND has_cart = 1)                   AS pv_cart,
            count(*) FILTER (WHERE has_pv = 1 AND has_fav = 1)                    AS pv_fav,
            count(*) FILTER (WHERE has_pv = 1 AND has_buy = 1)                    AS pv_buy,
            count(*) FILTER (WHERE has_cart = 1 AND has_buy = 1)                  AS cart_buy,
            count(*) FILTER (WHERE has_fav = 1 AND has_buy = 1)                   AS fav_buy,
            count(*) FILTER (WHERE (has_cart = 1 OR has_fav = 1))                 AS intent,
            count(*) FILTER (WHERE (has_cart = 1 OR has_fav = 1) AND has_buy = 1) AS intent_buy
        FROM read_parquet('{uf}')
        """
    ).fetchone()
    con.close()
    cols = ["pv", "cart", "fav", "buy", "pv_cart", "pv_fav", "pv_buy",
            "cart_buy", "fav_buy", "intent", "intent_buy"]
    return pd.DataFrame([row], columns=cols)


def run_overall() -> pd.DataFrame:
    o = _overall().iloc[0]
    stages = [
        ("pv", "浏览", o["pv"]),
        ("cart", "加购", o["cart"]),
        ("fav", "收藏", o["fav"]),
        ("intent", "加购或收藏", o["intent"]),
        ("buy", "购买", o["buy"]),
    ]
    df = pd.DataFrame(stages, columns=["stage", "stage_name", "users"])

    total_pv = o["pv"]
    rates = {
        "pv→cart 加购率": o["pv_cart"] / total_pv,
        "pv→fav 收藏率": o["pv_fav"] / total_pv,
        "pv→buy 整体购买转化率": o["pv_buy"] / total_pv,
        "cart→buy 加购购买率": o["cart_buy"] / o["cart"],
        "fav→buy 收藏购买率": o["fav_buy"] / o["fav"],
        "intent→buy 意向购买率": o["intent_buy"] / o["intent"],
    }
    rates_df = pd.DataFrame(
        [{"path": k, "conversion_rate": v} for k, v in rates.items()]
    )

    print("=== 总体漏斗（按去重用户） ===")
    print(df.to_string(index=False))
    print("\n=== 各环节转化率 ===")
    print(rates_df.assign(conversion_rate=lambda x: (x.conversion_rate * 100).round(2)).to_string(index=False))
    return df, rates_df


def run_event_funnel() -> pd.DataFrame:
    """事件级漏斗（行为次数口径），体现各环节流失率。"""
    con = etl.connect()
    p = config.CLEAN_PARQUET.as_posix()
    cnt = con.execute(
        f"""
        SELECT behavior_type, count(*) AS events
        FROM read_parquet('{p}')
        GROUP BY 1
        """
    ).fetchdf().set_index("behavior_type")["events"].to_dict()
    con.close()

    stages = [
        ("pv", "浏览", cnt.get("pv", 0)),
        ("intent", "加购/收藏", cnt.get("cart", 0) + cnt.get("fav", 0)),
        ("cart", "加购", cnt.get("cart", 0)),
        ("fav", "收藏", cnt.get("fav", 0)),
        ("buy", "购买", cnt.get("buy", 0)),
    ]
    df = pd.DataFrame(stages, columns=["stage", "stage_name", "events"])

    pv = cnt.get("pv", 0)
    intent = cnt.get("cart", 0) + cnt.get("fav", 0)
    buy = cnt.get("buy", 0)
    paths = pd.DataFrame(
        [
            {"path": "pv→intent 浏览→加购/收藏", "conversion_rate": intent / pv,
             "loss_rate": 1 - intent / pv},
            {"path": "pv→cart 浏览→加购", "conversion_rate": cnt.get("cart", 0) / pv,
             "loss_rate": 1 - cnt.get("cart", 0) / pv},
            {"path": "pv→buy 浏览→购买", "conversion_rate": buy / pv, "loss_rate": 1 - buy / pv},
            {"path": "intent→buy 加购/收藏→购买", "conversion_rate": buy / intent,
             "loss_rate": 1 - buy / intent},
            {"path": "cart→buy 加购→购买", "conversion_rate": buy / cnt.get("cart", 0),
             "loss_rate": 1 - buy / cnt.get("cart", 0)},
            {"path": "fav→buy 收藏→购买", "conversion_rate": buy / cnt.get("fav", 0),
             "loss_rate": 1 - buy / cnt.get("fav", 0)},
        ]
    )
    print("=== 事件级漏斗（行为次数） ===")
    print(df.to_string(index=False))
    print("\n=== 事件级转化率 / 流失率 ===")
    show = paths.copy()
    show["conversion_rate"] = (show["conversion_rate"] * 100).round(2)
    show["loss_rate"] = (show["loss_rate"] * 100).round(2)
    print(show.to_string(index=False))
    return df, paths


def run_daily() -> pd.DataFrame:
    con = etl.connect()
    p = config.CLEAN_PARQUET.as_posix()
    raw = con.execute(
        f"""
        SELECT event_date AS date, behavior_type, count(DISTINCT user_id) AS users
        FROM read_parquet('{p}')
        GROUP BY 1, 2
        """
    ).fetchdf()
    con.close()

    piv = raw.pivot(index="date", columns="behavior_type", values="users").fillna(0).astype(int)
    piv = piv.reindex(columns=["pv", "cart", "fav", "buy"]).fillna(0).astype(int)
    piv = piv.reset_index()
    piv["pv_to_buy_rate"] = (piv["buy"] / piv["pv"] * 100).round(2)
    piv["pv_to_cart_rate"] = (piv["cart"] / piv["pv"] * 100).round(2)

    print("\n=== 按日漏斗 ===")
    print(piv.to_string(index=False))
    return piv


def run_category_top(n: int = 10) -> pd.DataFrame:
    con = etl.connect()
    p = config.CLEAN_PARQUET.as_posix()
    raw = con.execute(
        f"""
        SELECT category_id, behavior_type, count(DISTINCT user_id) AS users
        FROM read_parquet('{p}')
        GROUP BY 1, 2
        """
    ).fetchdf()
    con.close()

    piv = raw.pivot(index="category_id", columns="behavior_type", values="users").fillna(0).astype(int)
    piv = piv.reindex(columns=["pv", "cart", "fav", "buy"]).fillna(0).astype(int)
    piv = piv.sort_values("buy", ascending=False).head(n).reset_index()
    piv["pv_to_buy_rate"] = (piv["buy"] / piv["pv"] * 100).round(2)

    print(f"\n=== TOP{n} 类目（按购买用户数） ===")
    print(piv.to_string(index=False))
    return piv


def run_hour() -> pd.DataFrame:
    con = etl.connect()
    p = config.CLEAN_PARQUET.as_posix()
    df = con.execute(
        f"""
        SELECT hour, behavior_type, count(*) AS cnt
        FROM read_parquet('{p}')
        GROUP BY 1, 2
        """
    ).fetchdf()
    con.close()
    piv = df.pivot(index="hour", columns="behavior_type", values="cnt").fillna(0).astype(int)
    piv = piv.reindex(columns=["pv", "cart", "fav", "buy"]).fillna(0).astype(int).reset_index()
    return piv


def export() -> None:
    config.OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    event_df, event_paths = run_event_funnel()
    event_df.to_csv(config.OUTPUT_TABLES / "funnel_event_level.csv", index=False, encoding="utf-8-sig")
    event_paths.to_csv(config.OUTPUT_TABLES / "funnel_event_conversion.csv", index=False, encoding="utf-8-sig")

    overall, rates = run_overall()
    overall.to_csv(config.OUTPUT_TABLES / "funnel_overall.csv", index=False, encoding="utf-8-sig")
    rates.to_csv(config.OUTPUT_TABLES / "funnel_conversion_rates.csv", index=False, encoding="utf-8-sig")
    run_daily().to_csv(config.OUTPUT_TABLES / "funnel_daily.csv", index=False, encoding="utf-8-sig")
    run_category_top().to_csv(config.OUTPUT_TABLES / "funnel_category_top10.csv", index=False, encoding="utf-8-sig")
    run_hour().to_csv(config.OUTPUT_TABLES / "behavior_hour.csv", index=False, encoding="utf-8-sig")
    print("\n漏斗分析结果已导出至 output/tables/")
