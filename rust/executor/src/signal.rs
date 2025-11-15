use std::sync::Arc;

use async_nats::jetstream::Context;
use futures::StreamExt;
use serde::Deserialize;
use thiserror::Error;
use tracing::{debug, info};
use uuid::Uuid;

use crate::mode::{ExecutionMode, ModeController};
use crate::storage::SignalStore;

#[derive(Debug, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct TradeSignal {
    pub signal_id: Uuid,
    pub ts: String,
    pub strategy_id: String,
    pub symbol: String,
    pub side: String,
    pub size: f64,
    pub order_type: String,
    pub limit_price: f64,
    pub slippage_tolerance: f64,
}

#[derive(Debug)]
pub struct SignalEnvelope {
    pub message: TradeSignal,
}

#[derive(Debug, Error)]
pub enum SignalError {
    #[error("nats error: {0}")]
    Nats(#[from] async_nats::Error),
    #[error("serde error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("storage error: {0}")]
    Storage(#[from] crate::storage::StorageError),
}

impl SignalError {
    pub fn is_transient(&self) -> bool {
        matches!(self, SignalError::Nats(_) | SignalError::Json(_))
    }
}

pub struct SignalProcessor {
    js: Context,
    store: Arc<SignalStore>,
    mode: Arc<ModeController>,
    consumer: Option<async_nats::jetstream::consumer::pull::Consumer>,
}

impl SignalProcessor {
    pub fn new(js: Context, store: Arc<SignalStore>, mode: Arc<ModeController>) -> Self {
        Self { js, store, mode, consumer: None }
    }

    pub async fn poll(&mut self) -> Result<(), SignalError> {
        if self.consumer.is_none() {
            let consumer = self.js.pull_subscribe("signal.*", "executor").await?;
            self.consumer = Some(consumer);
        }

        let consumer = self.consumer.as_mut().expect("consumer initialised");
        let mut messages = consumer.fetch().max_messages(20).messages().await?;

        while let Some(message) = messages.next().await {
            let message = message?;
            let payload = message.payload.clone();
            let envelope = self.decode(&payload)?;
            if self.handle_signal(&envelope).await? {
                message.ack().await?;
            } else {
                message.ack().await?;
            }
        }

        Ok(())
    }

    fn decode(&self, payload: &[u8]) -> Result<SignalEnvelope, SignalError> {
        let message: TradeSignal = serde_json::from_slice(payload)?;
        Ok(SignalEnvelope { message })
    }

    async fn handle_signal(&self, envelope: &SignalEnvelope) -> Result<bool, SignalError> {
        let signal = &envelope.message;
        debug!(?signal, "executor.received_signal");
        if !self.store.ensure_processed(signal.signal_id).await? {
            debug!(%signal.signal_id, "executor.duplicate_signal");
            return Ok(false);
        }

        match self.mode.current() {
            ExecutionMode::Live => self.execute_live(signal).await?,
            ExecutionMode::Paper => self.execute_paper(signal).await?,
        }

        Ok(true)
    }

    async fn execute_live(&self, signal: &TradeSignal) -> Result<(), SignalError> {
        info!(?signal, "executor.execute_live");
        Ok(())
    }

    async fn execute_paper(&self, signal: &TradeSignal) -> Result<(), SignalError> {
        info!(?signal, "executor.execute_paper");
        Ok(())
    }
}
