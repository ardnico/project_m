# IG Price Poller

This project is a minimal IG market data poller. It logs into IG's REST API, repeatedly fetches bid/ask snapshots for configured epics, and records both authentication tokens and prices in a local SQLite database.

## How it trades
- **Authentication first:** `src/infra/ig_client.py` logs in with your API key, username, and password, storing CST and security tokens before any price requests are sent.
- **Price pulls, not orders:** The app only **polls** prices; it never places trades. `PricePoller` cycles through each epic, fetches the latest bid/ask, computes the mid price, and saves it with a timestamp.
- **Resilience:** Authentication failures halt the run so you can fix credentials; transient API errors are logged and retried on the next loop.
- **Persistence:** Session tokens and every price snapshot are stored via `src/infra/db.py` in SQLite so you can audit what the poller saw.

## Configuration
Settings can come from a YAML/TOML file plus `IG_` environment variables (env vars override file values).

Minimal YAML example:
```yaml
api_key: "your-api-key"
username: "your-username"
password: "your-password"
epics: ["CS.D.BITCOIN.TODAY.IP", "IX.D.DAX.IFMM.IP"]
polling_interval_seconds: 2
ig_base_url: "https://demo-api.ig.com/gateway/deal"
db_path: "data/trading.db"
log_level: "INFO"
demo_mode: false
demo_starting_balance: 100000
```

Supported environment overrides:
- `IG_API_KEY`, `IG_USERNAME`, `IG_PASSWORD`
- `IG_BASE_URL`, `IG_POLLING_INTERVAL_SECONDS`, `IG_DB_PATH`, `IG_LOG_LEVEL`
- `IG_DEMO_MODE`, `IG_DEMO_STARTING_BALANCE`, `IG_DEMO_PRICE_SEED`

## Running
1. Install dependencies (Python 3.11+):
   ```bash
   pip install -r requirements.txt
   ```
2. Provide settings via a config file and/or `.env` with the `IG_` variables.
3. Start the poller:
   ```bash
   python -m src.main --config config.yaml
   ```
4. To run offline with synthetic prices and a fictional balance, enable demo mode:
   ```bash
   python -m src.main --config config.yaml --demo
   ```
5. For a single login + fetch without looping, use dry run:
   ```bash
   python -m src.main --config config.yaml --dry-run
   ```

## Data storage
- Database path defaults to `data/trading.db`; it is created with `sessions` and `prices` tables if missing.
- Each `prices` row records the epic, bid, ask, mid, and UTC timestamp so downstream analytics can reconstruct market states.

## Observing behavior
- Increase log verbosity with `log_level: DEBUG` to see request flow and retries.
- The polling loop sleeps `polling_interval_seconds` between cycles; adjust for your rate limits and data freshness needs.
