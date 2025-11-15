# FX Automated Trading System Skeleton

This repository contains the foundational components for the FX automated
trading system described in the implementation plan.  The code base is split
between Python strategy logic and a Rust execution engine while relying on
NATS JetStream for messaging and PostgreSQL/SQLite for persistence.

## Layout

```
python/          Python package providing collectors, signal strategies and
                 backtest execution helpers.
rust/executor/   Rust crate implementing the execution engine and risk
                 controls.
protos/          Shared protobuf definitions.
```

## Getting Started

1. Install Python dependencies using `pip install -e python`.
2. Run the sample unit tests with `pytest -q` from the repository root.
3. Build the Rust executor with `cargo build -p executor` (see below).

## Messaging Contract

All communication between components happens through NATS JetStream.  The
current Python implementation serializes payloads as JSON while keeping the
protobuf schema in `python/protos/trade_signal.proto` to retain wire
compatibility with the Rust executor once code generation is wired into CI.

## Backtest Feedback Loop

The `fxbot.backtest.execution` module models the latency, slippage and rejection
behaviour observed in live trading and can be parameterised with data exported
from production metrics.

## Next Steps

* Flesh out Collector implementations for IG/OANDA APIs.
* Extend the executor to persist signal identifiers and manage live/paper
  transitions atomically.
* Provide Docker Compose definitions for local integration testing.
