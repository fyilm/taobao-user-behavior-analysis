import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import etl, features, funnel, rfm


def main() -> None:
    print("=" * 60)
    print("[1/4] 数据清洗")
    etl.clean()
    print("\n[2/4] 用户特征聚合")
    features.build()
    print("\n[3/4] 漏斗分析")
    funnel.export()
    print("\n[4/4] RFM 用户分层")
    rfm.export()
    print("=" * 60)
    print("全流程完成，结果在 output/tables/")


if __name__ == "__main__":
    main()
