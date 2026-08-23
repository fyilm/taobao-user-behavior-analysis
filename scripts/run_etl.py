import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import etl

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        etl.clean()
    else:
        etl.run_overview()
