from pathlib import Path

from otc_audit.warehouse import complete_validation, open_warehouse, register_batch

SCHEMA = Path(__file__).parents[1] / "sql" / "warehouse_schema.sql"


def test_duplicate_file_is_not_registered_twice(tmp_path):
    connection = open_warehouse(tmp_path / "audit.duckdb", SCHEMA)
    first, created = register_batch(connection, Path("source.xlsx"), "abc")
    second, replay_created = register_batch(connection, Path("source.xlsx"), "abc")
    assert created is True
    assert replay_created is False
    assert first == second


def test_validation_counts_are_recorded(tmp_path):
    connection = open_warehouse(tmp_path / "audit.duckdb", SCHEMA)
    batch, _ = register_batch(connection, Path("source.xlsx"), "abc")
    complete_validation(connection, batch, {"source_rows": 10, "accepted_rows": 8, "rejected_rows": 2})
    assert connection.execute("SELECT status, accepted_rows FROM batch_run").fetchone() == ("VALIDATED", 8)
