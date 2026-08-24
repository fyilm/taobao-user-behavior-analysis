# 淘宝用户行为数据分析

基于阿里天池「淘宝用户行为数据集」（约 1 亿条）的电商用户行为分析项目：数据清洗 → 漏斗分析 → RFM 用户价值分层 → Tableau 可视化 → 策略建议。

## 技术栈
- **SQL**：DuckDB（嵌入式列式引擎，直接对 CSV/Parquet 跑标准 SQL）
- **Python**：Pandas（聚合后小表精细分析）
- **依赖管理**：uv
- **版本管理**：Git（原始数据与中间 parquet 不进仓库）
- **可视化**：Tableau（数据源见 `output/tables/`，设计说明见 `docs/tableau_design.md`）

## 目录结构
```
taobaouserbehavier/
├── data/raw/           # 原始 CSV（3.67GB，不进 git）
├── data/processed/     # 清洗后 parquet + 用户特征表（不进 git）
├── sql/                # 数据探查 / 漏斗 / RFM 的 SQL
├── src/                # etl / features / funnel / rfm 模块
├── scripts/            # 各步骤入口脚本
├── output/tables/      # Tableau 就绪 CSV（小文件入库）
└── docs/               # 分析报告 + Tableau 设计说明
```

## 快速开始

```bash
# 1. 将 UserBehavior.csv 放入 data/raw/（已存在则跳过）
# 2. 安装依赖
uv sync

# 3. 运行全流程（清洗 → 特征 → 漏斗 → RFM）
uv run python scripts/run_all.py

# 或分步运行
uv run python scripts/run_etl.py          # 数据清洗
uv run python scripts/run_funnel.py       # 漏斗分析
uv run python scripts/run_rfm.py          # RFM 分层
```

## 主要结论

- **漏斗**：浏览→加购流失率高达 93.8%（事件级），是最大流失断层；收藏→购买转化 69.8% 远高于加购→购买 36.5%。
- **RFM**：「一般价值客户 + 一般发展客户」合计 53.7%，高频/活跃但购买极少，是核心转化洼地。
- **类目**：存在「高流量低转化」类目（转化率仅 4%~6%），流量与转化效率不匹配。
- **时间**：晚间 20:00–22:00 为流量高峰，周末流量大但转化低。

详细分析与策略建议见 `docs/analysis_report.md`，各表字段含义见 `docs/data_dictionary.md`。

## 数据说明
- 原始数据无表头，字段为 `user_id, item_id, category_id, behavior_type, timestamp(Unix 秒)`。
- 无金额字段，RFM 的 M 以「购买次数」作代理。
- 时间窗口：2017-11-25 ~ 2017-12-03（9 天）。
