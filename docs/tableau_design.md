# Tableau 可视化设计说明

数据源：`output/tables/` 下的 CSV（已用 `utf-8-sig` 编码，Tableau 可直接连接）。

## 数据源清单

| 文件 | 用途 | 粒度 |
|------|------|------|
| `funnel_event_level.csv` | 事件级漏斗各环节行为次数 | 环节 |
| `funnel_event_conversion.csv` | 事件级转化率/流失率 | 路径 |
| `funnel_overall.csv` | 用户级漏斗各环节去重用户数 | 环节 |
| `funnel_conversion_rates.csv` | 用户级转化率 | 路径 |
| `funnel_daily.csv` | 每日用户漏斗 + 转化率 | 日期 |
| `funnel_category_top10.csv` | TOP10 类目漏斗 | 类目 |
| `behavior_hour.csv` | 各行为 24 小时分布 | 小时 |
| `rfm_segments.csv` | RFM 8 分群汇总 | 分群 |
| `rfm_score_distribution.csv` | RFM 分数组合分布 | 分数组合 |
| `rfm_user_level.csv` | 用户级 RFM 明细（钻取用，59MB） | 用户 |

## 仪表盘设计（建议 3 个 Sheet / 1 个 Dashboard）

### 仪表盘 1：用户行为漏斗

**图 1.1 事件级漏斗（漏斗图）**
- 数据源：`funnel_event_level.csv`
- 图表类型：漏斗图（或水平条形）
- 步骤/维度：`stage_name`（浏览 → 加购/收藏 → 购买）
- 度量：`events`（SUM）
- 说明：体现「浏览→加购 流失 93.8%」「加购→购买 流失 63.6%」等流失点

**图 1.2 转化率/流失率对比（条形图）**
- 数据源：`funnel_event_conversion.csv`
- 行：`path`；列：`conversion_rate`、`loss_rate`（* 100 显示为 %）
- 双轴或分组条形，突出高流失环节

**图 1.3 每日转化趋势（折线图）**
- 数据源：`funnel_daily.csv`
- 列：`date`（日期）；行：`pv_to_buy_rate`、`pv_to_cart_rate`
- 说明：12-01 加购率最高（36.4%），周末（12-02/03）流量大但购买转化率略降

**图 1.4 24 小时行为分布（面积/折线图）**
- 数据源：`behavior_hour.csv`
- 列：`hour`（0-23）；行：`pv`、`buy`（可加 `cart`、`fav`）
- 说明：晚间 20:00-22:00 为流量高峰，凌晨 2:00-6:00 低谷

### 仪表盘 2：TOP 类目洞察

**图 2.1 TOP10 类目购买用户数（条形图）**
- 数据源：`funnel_category_top10.csv`
- 行：`category_id`（维度）；列：`buy`（SUM）

**图 2.2 类目转化率 vs 流量（散点图）**
- 数据源：`funnel_category_top10.csv`
- X：`pv`（SUM）；Y：`pv_to_buy_rate`（AVG）；标记：`category_id`
- 说明：识别「高流量低转化」类目（如 1320293、4756105）做优化

### 仪表盘 3：RFM 用户价值分层

**图 3.1 分群规模（条形图 / 环形图）**
- 数据源：`rfm_segments.csv`
- 行：`segment`；列：`users`（SUM）；颜色：`pct`

**图 3.2 分群画像（气泡图 / 表）**
- 数据源：`rfm_segments.csv`
- X：`avg_frequency`；Y：`avg_monetary`；大小：`users`；标签：`segment`
- 说明：右下角「一般价值客户」高频低购买，为转化重点

**图 3.3 RFM 分数组合分布（热力图）**
- 数据源：`rfm_score_distribution.csv`
- 行：`r_score`；列：`f_score`（或 `m_score`）；颜色：`users`

## 配色与交互建议
- 流失/低转化用红色系，转化/高价值用绿色系，中性用蓝灰
- 漏斗图各环节按顺序用同一色相的渐变
- 添加筛选器：`segment`、`category_id`（跨 Sheet 联动）
