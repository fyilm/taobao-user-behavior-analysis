from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
SQL_DIR = ROOT / "sql"
OUTPUT_TABLES = ROOT / "output" / "tables"
OUTPUT_FIGURES = ROOT / "output" / "figures"
DOCS = ROOT / "docs"

RAW_CSV = DATA_RAW / "UserBehavior.csv"
CLEAN_PARQUET = DATA_PROCESSED / "user_behavior_clean.parquet"

COLUMNS = {
    "user_id": "BIGINT",
    "item_id": "BIGINT",
    "category_id": "BIGINT",
    "behavior_type": "VARCHAR",
    "ts": "BIGINT",
}

BEHAVIOR_TYPES = ("pv", "buy", "cart", "fav")

for _d in (DATA_RAW, DATA_PROCESSED, SQL_DIR, OUTPUT_TABLES, OUTPUT_FIGURES, DOCS):
    _d.mkdir(parents=True, exist_ok=True)
