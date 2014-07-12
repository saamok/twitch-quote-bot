import logging


def _get_formatter():
    """Return a nice common log formatter"""

    return logging.Formatter('%(asctime)s [%(levelname)8s] %(message)s')


def _get_log():
    """Set up a basic logger"""

    logger = logging.getLogger('TwitchBot')
    logger.setLevel(logging.CRITICAL)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    ch.setFormatter(_get_formatter())

    logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)

    return logger


log = _get_log()


def set_log_file(log_file):
    """Configure the logger above to log to a file"""

    fh = logging.FileHandler(log_file)

    fh.setLevel(logging.DEBUG)
    fh.setFormatter(_get_formatter())

    log.addHandler(fh)
