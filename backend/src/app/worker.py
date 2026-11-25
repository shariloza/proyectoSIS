"""Proceso worker de re-entrenamiento: `python -m app.worker`."""

import signal
import tempfile
import threading
from pathlib import Path
from types import FrameType

from app.config import get_settings
from app.modules.training.application.worker import TrainingWorker
from app.shared.database import create_session_factory
from app.shared.logging import configure_logging

POLL_SECONDS = 3.0
HEARTBEAT_FILE = Path(tempfile.gettempdir()) / "worker-heartbeat"


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    stop = threading.Event()

    def handle_signal(_signum: int, _frame: FrameType | None) -> None:
        stop.set()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    worker = TrainingWorker(
        create_session_factory(settings.database_url),
        settings.artifacts_dir,
        settings.training_timeout_seconds,
    )
    worker.run_forever(POLL_SECONDS, stop.is_set, HEARTBEAT_FILE)


if __name__ == "__main__":
    main()
