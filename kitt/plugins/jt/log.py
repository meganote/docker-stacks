import logging
import logging.handlers

logger = logging.getLogger("livekit.plugins.jt")
logger.setLevel(logging.DEBUG)

logger_fh = logging.handlers.RotatingFileHandler(
    "app.log", mode="a", maxBytes=100 * 1024 * 1024, backupCount=10
)
logger_ch = logging.StreamHandler()
logger_formatter = logging.Formatter(
    "%(asctime)s - %(threadName)s - %(module)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s"
)

logger_ch.setFormatter(logger_formatter)
logger_fh.setFormatter(logger_formatter)

logger.addHandler(logger_ch)
logger.addHandler(logger_fh)

logger.propagate = False
