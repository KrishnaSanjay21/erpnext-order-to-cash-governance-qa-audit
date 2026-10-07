param(
    [switch]$ForceDownload
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    if ($ForceDownload) {
        python -m otc_audit.cli acquire --force
    } else {
        python -m otc_audit.cli acquire
    }
    python -m otc_audit.cli validate
    python -m otc_audit.cli build-audit
    python scripts/build_dashboard_data.py
    python -m pytest
    ruff check .
} finally {
    Pop-Location
}

