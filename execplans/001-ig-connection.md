# IGデモ口座接続と価格ポーリング基盤

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. Maintain this plan in accordance with `.agent/PLANS.md` at the repository root; this file must stay self-contained for a novice contributor.

## Purpose / Big Picture

The goal is to stand up a minimal but durable pipeline that authenticates against the IG demo environment, polls current prices at a fixed cadence, and exposes the results in a form the rest of the system can consume. After completion, a user can start the app with a local configuration file, watch logs showing successful authentication and periodic price fetches, and see persisted tick snapshots in a SQLite database. This establishes the foundation for later strategy and order execution work.

## Progress

- [x] (2025-02-05 00:00Z) Draft ExecPlan skeleton with scope, orientation, and acceptance criteria.
- [x] (2025-02-05 00:45Z) Initial repository bootstrap: created Python package layout under `src/` with config, infra client, and app runner modules.
- [x] (2025-02-05 00:55Z) Implemented configuration loading (env + file) and secrets handling for IG credentials.
- [x] (2025-02-05 01:10Z) Built IG REST client for login and price polling with retry/backoff and logging hooks.
- [x] (2025-02-05 01:20Z) Implemented SQLite persistence for account session tokens and polled prices.
- [x] (2025-02-05 01:25Z) Added CLI entrypoint to start polling loop with graceful shutdown and dry-run option.
- [x] (2025-02-05 01:35Z) Provided unit tests covering config parsing, client error handling, and polling loop logic (with HTTP stubs).
- [ ] Validate end-to-end by running polling loop against a stub server and documenting expected logs/db rows.
- [ ] Outcomes & Retrospective updated after validation.

## Surprises & Discoveries

- Observation: None yet.
  Evidence: N/A.
- Observation: Package installation from PyPI is blocked by proxy (HTTP 403) in this environment, preventing dependency setup.
  Evidence: `pip install -r requirements.txt` fails with Tunnel connection failed 403.

## Decision Log

- Decision: Use requests + backoff-based retry for initial REST calls instead of async stack to reduce complexity.
  Rationale: MVP prioritizes reliability over throughput; sync calls are simpler to test and deploy in systemd context.
  Date/Author: 2025-02-05 / agent.

## Outcomes & Retrospective

(To be updated after validation. Summarize whether polling is stable, what failure modes were observed, and any open gaps.)

## Context and Orientation

Current repository has no Python source yet. Target structure, relative to repo root:
- `src/main.py`: CLI entrypoint starting the polling service.
- `src/config/loader.py`: Reads YAML/TOML config merged with environment variables; validates via pydantic BaseSettings.
- `src/infra/ig_client.py`: Handles IG REST login (session creation), token refresh, and price polling for one market (epic code provided in config).
- `src/infra/db.py`: SQLite connection factory and simple repositories for sessions and prices.
- `src/app/price_poller.py`: Loop that calls the client on a schedule, persists results, and respects stop signals.
- `tests/`: Unit tests with HTTP mocking (responses library) and temporary SQLite DB.

Terminology used here:
- "epic": IG market identifier string (e.g., "CS.D.EURUSD.MINI.IP").
- "CST" and "X-SECURITY-TOKEN": session tokens returned by IG REST login; both required on subsequent requests.
- "Price snapshot": timestamped bid/ask mid values for a single epic fetched via REST /prices endpoint.

## Plan of Work

Describe edits in order, referencing full paths.

1) Create Python package skeleton under `src/` with `__init__.py` files to allow imports. Add `pyproject.toml` or `requirements.txt` listing dependencies: `pydantic`, `requests`, `python-dotenv`, `responses`, `sqlite3` (stdlib).
2) Implement `src/config/loader.py` with a `Settings` class (pydantic BaseSettings) capturing IG host URL (demo), API key, username, password, epic list, polling interval seconds, database path, and log level. Provide `load_settings()` function reading `.env` and optional YAML/TOML file path, merging env to override file values.
3) Implement `src/infra/secrets.py` to load credentials from environment or `.env` while ensuring secrets are not logged. Include helper to redact values in logs.
4) Implement `src/infra/db.py` with functions to initialize SQLite schema: tables `sessions` (id, cst, security_token, created_at) and `prices` (id, epic, bid, ask, mid, timestamp). Provide context-managed connection and repository helpers `store_session(tokens)` and `store_price(snapshot)`.
5) Implement `src/infra/ig_client.py` using `requests.Session`. Expose methods `login()` returning session tokens, and `fetch_price(epic: str)` returning a dataclass `PriceSnapshot` with bid/ask/mid/timestamp. Add retry with exponential backoff (e.g., using `tenacity` or manual loop) on network errors and 5xx; treat 401/403 as fatal requiring manual intervention. Include detailed logging and mapping of IG REST endpoints (POST /session for login; GET /prices/{epic}?fields=BID,ASK&resolution=SECOND&max=1`).
6) Implement `src/app/price_poller.py` with a `PricePoller` class taking settings, ig_client, db_repo, and logger. Loop sleeps per interval, calls `fetch_price` for each epic, persists via db, logs success/failures, and stops on keyboard interrupt or fatal auth errors. Ensure graceful shutdown closes DB and HTTP session.
7) Implement `src/main.py` as CLI using argparse: options for config file path and once-off test mode. In normal mode, load settings, initialize logging (basic config with rotation stub), construct components, perform login (store tokens), and start poller. Provide `--dry-run` to only validate config and IG login once.
8) Add tests under `tests/`: `test_config_loader.py` (env overrides file), `test_ig_client.py` (login and price handling using responses to stub HTTP), `test_price_poller.py` (loop with stub client verifying persistence). Use temporary directories and SQLite `:memory:`.
9) Document validation steps in `Concrete Steps`: how to run unit tests and a local demo that hits a stub server (e.g., using responses to simulate). Update `Outcomes & Retrospective` once done.

## Concrete Steps

Commands assume working directory `/workspace/project_m`.

- Create virtual environment and install dependencies:
  - `python3 -m venv .venv`
  - `source .venv/bin/activate`
  - `pip install -U pip`
  - `pip install pydantic requests python-dotenv responses tenacity`
- Run unit tests:
  - `pytest -q`
- Launch poller in dry run (once login and one price fetch):
  - `python -m src.main --config ./config/example.yaml --dry-run`
- Launch continuous poller:
  - `python -m src.main --config ./config/example.yaml`
- Inspect SQLite contents:
  - `sqlite3 data/trading.db 'select count(*) from prices;'`

Expected outputs to confirm success:
- Logs show "IG login succeeded" once and recurring "fetched price" entries per epic at the configured interval.
- SQLite `prices` table grows over time; schema matches plan.
- In tests, HTTP stubs receive requests with both CST and X-SECURITY-TOKEN headers.

## Validation and Acceptance

- All unit tests under `tests/` pass locally.
- In dry-run mode, process exits after single login + price fetch with exit code 0 and tokens not logged in plaintext.
- In continuous mode (with stubbed responses), poller runs for at least three iterations without unhandled exceptions, persisting rows into SQLite with correct epic and timestamp ordering.
- Fatal auth errors (401/403) cause poller to stop and return non-zero exit, logged clearly.

## Idempotence and Recovery

- Polling loop can be restarted safely; SQLite insertions are append-only for snapshots. Schema initialization uses `IF NOT EXISTS` so reruns do not fail.
- If login fails due to network errors, retry with backoff; on consistent 4xx, exit gracefully so supervisor can restart after credentials are fixed.
- `.env` and config file are read each start, so credential rotation happens via restart without code changes.

## Artifacts and Notes

- Capture sample log excerpts after first successful run and place in `artifacts/ig-poller.log.example` for reference.
- Keep example config at `config/example.yaml` with placeholder credentials and comments indicating required secrets.

## Interfaces and Dependencies

- New dataclass `PriceSnapshot` in `src/infra/ig_client.py` with fields: `epic: str`, `bid: float`, `ask: float`, `mid: float`, `timestamp: datetime`.
- Functions:
  - `config.loader.load_settings(path: Optional[str]) -> Settings`
  - `infra.secrets.load_env(path: Optional[str]) -> Dict[str, str]`
  - `infra.db.init_db(path: str) -> sqlite3.Connection`
  - `infra.db.store_session(conn, tokens: Dict[str, str]) -> None`
  - `infra.db.store_price(conn, snapshot: PriceSnapshot) -> None`
  - `infra.ig_client.IGClient.login() -> Dict[str, str]`
  - `infra.ig_client.IGClient.fetch_price(epic: str) -> PriceSnapshot`
  - `app.price_poller.PricePoller.run(stop_event: threading.Event | None = None) -> None`
- Dependencies: `pydantic`, `requests`, `tenacity`, `python-dotenv`, `responses` (tests), Python stdlib modules `logging`, `sqlite3`, `argparse`, `dataclasses`, `time`, `threading`.

## Revision Note

2025-02-05: Initial creation of ExecPlan outlining IG demo authentication and REST polling foundation.
