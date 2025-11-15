use sqlx::{Pool, Sqlite, SqlitePool};
use thiserror::Error;
use tracing::info;
use uuid::Uuid;

#[derive(Debug, Error)]
pub enum StorageError {
    #[error("database error: {0}")]
    Database(#[from] sqlx::Error),
}

#[derive(Clone)]
pub struct SignalStore {
    pool: SqlitePool,
}

impl SignalStore {
    pub async fn new(database_url: &str) -> Result<Self, StorageError> {
        let pool = SqlitePool::connect(database_url).await?;
        sqlx::query(
            "CREATE TABLE IF NOT EXISTS processed_signals (
                signal_id TEXT PRIMARY KEY,
                processed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )",
        )
        .execute(&pool)
        .await?;

        Ok(Self { pool })
    }

    pub async fn ensure_processed(&self, signal_id: Uuid) -> Result<bool, StorageError> {
        let result = sqlx::query_scalar::<_, i64>(
            "SELECT COUNT(1) FROM processed_signals WHERE signal_id = ?",
        )
        .bind(signal_id.to_string())
        .fetch_one(&self.pool)
        .await?;

        if result > 0 {
            return Ok(false);
        }

        sqlx::query(
            "INSERT INTO processed_signals(signal_id) VALUES (?)",
        )
        .bind(signal_id.to_string())
        .execute(&self.pool)
        .await?;
        info!(%signal_id, "signal.persisted");
        Ok(true)
    }
}
