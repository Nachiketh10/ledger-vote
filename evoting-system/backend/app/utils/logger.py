import logging
import os
import sys


def configure_logger(app) -> None:
    """Attach a consistent formatter/handler setup to the Flask app logger."""
    log_level = logging.DEBUG if app.debug else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        )
    )

    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)

    # Optional file logging in production (directory must be writable)
    log_dir = os.getenv("LOG_DIR")
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(os.path.join(log_dir, "app.log"))
        file_handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
        )
        app.logger.addHandler(file_handler)
