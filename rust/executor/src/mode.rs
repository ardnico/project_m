use std::sync::Arc;

use parking_lot::RwLock;
use tracing::info;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ExecutionMode {
    Live,
    Paper,
}

impl Default for ExecutionMode {
    fn default() -> Self {
        ExecutionMode::Paper
    }
}

#[derive(Debug, Default)]
pub struct ModeController {
    mode: RwLock<ExecutionMode>,
}

impl ModeController {
    pub fn current(&self) -> ExecutionMode {
        *self.mode.read()
    }

    pub fn set(&self, next: ExecutionMode) {
        let mut lock = self.mode.write();
        if *lock != next {
            *lock = next;
            info!(?next, "mode.changed");
        }
    }

    pub fn downgrade_to_paper(&self) {
        self.set(ExecutionMode::Paper);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_mode_transitions() {
        let controller = ModeController::default();
        assert_eq!(controller.current(), ExecutionMode::Paper);
        controller.set(ExecutionMode::Live);
        assert_eq!(controller.current(), ExecutionMode::Live);
        controller.downgrade_to_paper();
        assert_eq!(controller.current(), ExecutionMode::Paper);
    }
}
