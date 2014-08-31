from math import floor
import logging


def _get_formatter():
    """
    Get a standard log output formatter

    :return: logging.Formatter instance
    """

    return logging.Formatter('%(asctime)s [%(levelname)8s] %(message)s')


def _get_log():
    """
    Set up a basic logger

    :return: logging.Logger instance
    """

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
    """
    Configure the logger to save the log contents to a file

    :param log_file: Path to the log file
    :return: None
    """

    fh = logging.FileHandler(log_file)

    fh.setLevel(logging.DEBUG)
    fh.setFormatter(_get_formatter())

    log.addHandler(fh)

def human_readable_time(seconds):
    """
    Returns the given number of seconds as human readable time

    >>> from bot.utils import human_readable_time
    >>> human_readable_time(60)
    '1 minute(s)'
    >>> human_readable_time((3600 * 2) + (60 * 2) + 2)
    '2 hour(s) 2 minute(s) 2 second(s)'

    :param seconds: The number of seconds
    :return: The human readable text
    """

    units = [
        ("year(s)", 60 * 60 * 24 * 365),
        ("month(s)", 60 * 60 * 24 * 30),
        ("week(s)", 60 * 60 * 24 * 7),
        ("day(s)", 60 * 60 * 24),
        ("hour(s)", 60 * 60),
        ("minute(s)", 60),
        ("second(s)", 1)
    ]

    values = []
    seconds = int(seconds)

    for key, unit_seconds in units:
        unit_count = int(floor(seconds / unit_seconds))
        if unit_count > 0:
            values.append("{0} {1}".format(
                unit_count, key
            ))
            seconds -= unit_seconds * unit_count

    output = " ".join(values)

    return output
