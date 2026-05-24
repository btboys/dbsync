from app.celery_app import celery_app

import app.worker.backup  # noqa: F401
import app.worker.restore  # noqa: F401
import app.worker.migration  # noqa: F401
