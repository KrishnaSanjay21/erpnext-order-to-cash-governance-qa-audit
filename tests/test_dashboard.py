from pathlib import Path

from otc_audit.dashboard import build_dashboard_facts
from tests.test_validation import sample
from otc_audit.validation import validate_transactions


def test_dashboard_facts_reconcile_to_validated_rows(tmp_path: Path):
    validated = validate_transactions(sample())
    result = build_dashboard_facts(validated, tmp_path)
    assert result["document_rows"] == 2
    assert (tmp_path / "fact_monthly_disposition.parquet").exists()
    assert (tmp_path / "fact_control_failures.parquet").exists()

