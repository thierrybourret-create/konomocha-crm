import logging
import logging.handlers
import os

# #10: use env var so staging/production can point to different log dirs
LOG_DIR = os.getenv("LOG_DIR", "/home/thierry/logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "kizuna.log")


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file: new file each midnight, keep 30 days
    file_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_FILE, when="midnight", interval=1, backupCount=30, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y-%m-%d"
    logger.addHandler(file_handler)

    # Also write to stdout so journalctl picks it up
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


app_logger = get_logger("kizuna")
