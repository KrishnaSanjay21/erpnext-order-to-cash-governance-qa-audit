# ERPNext local environment

This project pins the same ERPNext image used by the official `frappe_docker` single-compose example. It is an audit/demo environment, not a production topology.

1. Copy `.env.example` to `.env` and replace both development passwords.
2. Run `docker compose up -d`.
3. Open `http://localhost:8080` and complete the Setup Wizard for **UCI Retail Audit Ltd**, United Kingdom, GBP, and the retail chart of accounts.
4. Create a dedicated integration user and API key/secret; place only the secret values in `.env`.
5. Run `python scripts/configure_erpnext.py` to add lineage fields and roles.
6. Leave `submit_documents: false` for the first migration. Review the reconciliation, then enable submission for an approved sample or batch.

Persistent MariaDB, site, log, and Redis queue volumes make restart/recovery testing possible. `docker compose down` preserves them; only `docker compose down -v` deletes the environment.

Reference: the official [Frappe Docker repository](https://github.com/frappe/frappe_docker) and its [`pwd.yml`](https://github.com/frappe/frappe_docker/blob/main/pwd.yml).

