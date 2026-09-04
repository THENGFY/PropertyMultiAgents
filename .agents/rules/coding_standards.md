# Workspace Rules: PropertyMultiAgents Coding & Architectural Standards

## 1. Core Architecture
- **Framework**: FastAPI with asynchronous endpoints.
- **ORM & Database**: SQLAlchemy 2.0 async with `aiosqlite` (for development & testing) and `asyncpg` (for production PostgreSQL).
- **Data Validation**: Pydantic v2 schemas with strict typing.
- **Timezone Standardization**: All timestamps must use `datetime.now(timezone.utc)`.

## 2. CEA Ingestion & Pipeline Invariants
- **Registration Format**: Clean and validate CEA registration numbers using `^[RK]\d{6,7}[A-Z]$`.
- **Agency Licences**: Standardize to uppercase `^L\d{6,7}[A-Z]$`.
- **Market Segments**: Strict classification into `NEW_SALE`, `RESALE`, and `RENTAL`.
- **Deduplication**: Enforce compound unique constraints on `(agent_id, transaction_ref, transaction_date)`.
- **Rolling Window**: Trailing 12-Month window is defined as `[reference_date - 366 days, reference_date]`.

## 3. Testing & Verification Requirements
- All features must have 100% passing Pytest test coverage (`pytest -v tests/`).
- API latency SLA target: P95 < 50.0ms for ranking queries.
- Zero mock production test rule: unit tests must use deterministic synthetic fixture pipelines.
