mod mode;
mod signal;
mod storage;

use std::sync::Arc;

use async_nats::jetstream::Context;
use tokio::signal;
use tokio::time::{sleep, Duration};
use tracing::{error, info, instrument};

use crate::mode::ModeController;
use crate::signal::SignalProcessor;
use crate::storage::SignalStore;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    init_tracing();

    let js = connect_jetstream().await?;
    let store = Arc::new(SignalStore::new("sqlite::memory:").await?);
    let mode = Arc::new(ModeController::default());

    let processor = SignalProcessor::new(js.clone(), store.clone(), mode.clone());
    let shutdown = tokio::spawn(async move {
        if let Err(err) = run_signal_loop(processor).await {
            error!(?err, "signal loop exited with error");
        }
    });

    signal::ctrl_c().await?;
    info!("shutdown", "received ctrl_c" = true);
    shutdown.abort();
    Ok(())
}

fn init_tracing() {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .with_target(false)
        .init();
}

async fn connect_jetstream() -> anyhow::Result<Context> {
    let client = async_nats::connect("nats://127.0.0.1:4222").await?;
    Ok(async_nats::jetstream::new(client))
}

#[instrument(skip(processor))]
async fn run_signal_loop(mut processor: SignalProcessor) -> anyhow::Result<()> {
    loop {
        match processor.poll().await {
            Ok(_) => {}
            Err(err) if err.is_transient() => {
                error!(?err, "transient error during poll");
                sleep(Duration::from_secs(1)).await;
            }
            Err(err) => return Err(err.into()),
        }
    }
}
