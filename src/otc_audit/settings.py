"""Environment-driven runtime settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    erpnext_base_url: str = "http://localhost:8080"
    erpnext_api_key: str = "replace-me"
    erpnext_api_secret: str = "replace-me"
    erpnext_company: str = "UCI Retail Audit Ltd"
    erpnext_abbr: str = "URA"
    erpnext_warehouse: str = "Stores - URA"
    erpnext_cost_center: str = "Main - URA"
    erpnext_posting_mode: str = "draft"
    otc_data_dir: Path = Path("data")
    otc_control_db: Path = Path("warehouse/otc_audit.duckdb")

    @property
    def raw_dir(self) -> Path:
        return self.otc_data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.otc_data_dir / "processed"

    @property
    def reports_dir(self) -> Path:
        return self.otc_data_dir / "reports"

    def ensure_directories(self) -> None:
        for path in (self.raw_dir, self.processed_dir, self.reports_dir, self.otc_control_db.parent):
            path.mkdir(parents=True, exist_ok=True)

