from pathlib import Path

import pandas as pd

from otc_audit.dashboard import build_dashboard_facts


def main() -> None:
    root = Path(__file__).parents[1]
    validated = pd.read_parquet(root / "data" / "processed" / "validated_transactions.parquet")
    print(build_dashboard_facts(validated, root / "data" / "processed" / "dashboard"))


if __name__ == "__main__":
    main()

