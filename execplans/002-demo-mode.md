# デモモードと仮想資金サポート

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. Maintain this plan in accordance with `.agent/PLANS.md` at the repository root; this file must stay self-contained for a novice contributor.

## Purpose / Big Picture

Add a first-class demo mode that runs the poller without hitting IG endpoints, using synthetic prices and a configurable fictional balance. After completion, a user can launch the app with `demo_mode` enabled (via config or CLI), observe login/price logs generated locally, and see persisted prices and session rows that mirror production shape without requiring real credentials.

## Progress

- [x] (2025-02-05 00:00Z) Draft ExecPlan with scope, orientation, and acceptance criteria.
- [x] (2025-02-05 01:00Z) Implement configuration changes (demo_mode, balance, seed, CLI override) with validation rules updated.
- [x] (2025-02-05 01:20Z) Build demo client generating deterministic synthetic prices and exposing login tokens.
- [x] (2025-02-05 01:30Z) Wire main flow to choose demo client, log virtual balance, and keep DB/session persistence consistent.
- [x] (2025-02-05 01:40Z) Expand tests for settings parsing, demo client behavior, and end-to-end price persistence in demo mode.
- [x] (2025-02-05 01:50Z) Update docs and plan sections (Decision Log, Outcomes & Retrospective) after implementation and validation.

## Surprises & Discoveries

- Observation: None yet.
  Evidence: N/A.

## Decision Log

- Decision: Demo mode uses a dedicated `DemoIGClient` with deterministic random walk seeded via config to keep tests stable while mimicking price movement.
  Rationale: Keeps the interface identical to `IGClient` and allows reproducible expectations for tests and users.
  Date/Author: 2025-02-05 / agent.
- Decision: `load_settings` accepts CLI overrides so the `--demo` flag can bypass credential validation before instantiation.
  Rationale: Validation originally enforced credentials; merging the flag prior to dataclass creation avoids false failures when intentionally offline.
  Date/Author: 2025-02-05 / agent.

## Outcomes & Retrospective

Demo mode now runs end-to-end without external HTTP calls. Configuration accepts demo flags and fictional balance/seed, with CLI override enabling the mode even when credentials are absent. The `DemoIGClient` produces deterministic synthetic prices and tokens, and the polling loop persists them to SQLite identically to the real client. All unit tests pass, covering config parsing, demo client behavior, and poller integration. No blocking gaps remain for offline usage; future work could expose the virtual balance in logs or metrics more prominently.

## Context and Orientation

Current project is an IG price poller with CLI entrypoint `src/main.py`, configuration loader `src/config/loader.py`, synchronous IG REST client in `src/infra/ig_client.py`, SQLite helpers in `src/infra/db.py`, and polling loop `src/app/price_poller.py`. Tests live under `tests/` using `responses` for HTTP stubs. Settings currently require real credentials and default to the IG demo base URL. There is no offline mode or synthetic price generation.

We need a demo mode that avoids real HTTP calls yet preserves the same interfaces so existing pipeline (login -> store_session -> poll -> store_price) continues to work. Configuration must accept a fictional starting balance and optional randomness seed. CLI should allow forcing demo mode without editing files.

## Plan of Work

Describe edits in order with repository-relative paths.

1) Extend `src/config/loader.py` Settings with `demo_mode` (bool), `demo_starting_balance` (float), and `demo_price_seed` (int|None). Relax credential validation when `demo_mode` is True. Add env overrides (`IG_DEMO_MODE`, `IG_DEMO_STARTING_BALANCE`, `IG_DEMO_PRICE_SEED`) and CLI override flag handled in `src/main.py`.
2) Implement `src/infra/demo_client.py` providing a `DemoIGClient` with `login()` and `fetch_price()` mirroring `IGClient` signatures, returning dummy tokens and deterministic synthetic `PriceSnapshot` instances for requested epics. Include logger hooks and `close()` no-op.
3) Update `src/main.py` to parse a `--demo` flag, merge it into settings, select the appropriate client (real vs demo), log virtual balance/seed, and keep DB/session persistence intact.
4) Add tests: config parsing for demo flags/env; demo client price generation and token handling; price poller integration using `DemoIGClient` storing to SQLite. Ensure existing tests still pass.
5) Refresh README config examples and usage notes to explain demo mode and fictional balance. Update this ExecPlan sections (Progress, Decision Log, Outcomes) as work proceeds.

## Concrete Steps

Commands assume working directory `/workspace/project_m`.

- Run unit tests: `pytest -q`
- Launch poller in demo mode (once per epic) after implementation: `python -m src.main --config ./config.yaml --demo --dry-run`
- Standard poller run unchanged: `python -m src.main --config ./config.yaml`

## Validation and Acceptance

Acceptance criteria:
- Configuration loader accepts `demo_mode: true` without requiring API credentials and honors env/CLI overrides. Starting balance and seed parse correctly.
- Demo client returns deterministic, positive bid/ask/mid with ISO timestamps and records session tokens into SQLite when `store_session` is called.
- Running `PricePoller` with `DemoIGClient` for one iteration writes price rows to the database without external HTTP calls.
- CLI `--demo` flag forces demo mode even if config file omits it, and logs clearly state demo mode with the fictional balance value.
- All tests pass (`pytest -q`).

## Idempotence and Recovery

Demo mode is additive and does not alter production paths. Re-running setup or tests is safe. If demo mode is misconfigured, the loader should emit clear validation errors. Switching between demo and real modes only requires changing the flag; tokens and prices are stored in separate rows but share schema.

## Artifacts and Notes

Keep commit diff small and focused on config, client selection, and demo generator. Capture notable log snippets in Outcomes once validated.

## Interfaces and Dependencies

- `src/config/loader.Settings`: new fields `demo_mode: bool`, `demo_starting_balance: float`, `demo_price_seed: int | None`; `load_settings` merges env and CLI overrides and relaxes credential requirement when demo.
- `src/infra/demo_client.DemoIGClient`: methods `login() -> Dict[str, str]`, `fetch_price(epic: str) -> PriceSnapshot`, `close() -> None`; uses deterministic random walk per epic and `datetime.utcnow()` for timestamps.
- `src/main.parse_args`: add `--demo` flag; main selects `DemoIGClient` when active and logs balance/seed.
- Tests under `tests/` covering new behaviors and integration.

Note: This plan will be updated as progress is made and after validation to document outcomes and decisions.
