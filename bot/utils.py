from multiprocessing import Queue as MPQueue

try:
    from Queue import Queue
except ImportError:
    from queue import Queue

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


class CallData(object):
    """Describes a method call so it can be replicated"""

    def __init__(self, method, *args, **kwargs):
        self.method = method
        self.args = args
        self.kwargs = kwargs


class CallRelay(object):

    def __init__(self, logger=None, in_queue=None, out_queue=None):
        self.logger = logger
        self.in_queue = in_queue
        self.out_queue = out_queue

        self.call_object = None

    def set_call_object(self, call_object):
        if self.logger:
            self.logger.debug("Updated call object to {0}".format(
                type(call_object)
            ))
        self.call_object = call_object

    def stop(self):
        if self.logger:
            self.logger.debug("Stopping ChannelCall to {0}".format(
                type(self.call_object)
            ))
        self.in_queue.put(None)

    def _create_call_handler(self, name):
        def _handler(*args, **kwargs):
            if self.logger:
                self.logger.debug("ChannelCall call to {0}.{1}".format(
                    type(self.call_object),
                    name
                ))
            self.in_queue.put(CallData(name, *args, **kwargs))
            response = self.out_queue.get()
            if self.logger:
                self.logger.debug("ChannelCall response from {0}.{1}".format(
                    type(self.call_object),
                    name
                ))

            return response

        _handler.__name__ = name
        return _handler

    def __getattr__(self, name):
        return self._create_call_handler(name)

    def loop(self):
        while True:
            if self.logger:
                self.logger.debug("ChannelCall waiting for calls to {"
                                  "0}".format(
                    type(self.call_object)
                ))

            call = self.in_queue.get()

            if self.logger:
                self.logger.debug("ChannelCall for {0} got call".format(
                    type(self.call_object)
                ))

            # Magic message telling us to stop
            if call is None:
                if self.logger:
                    self.logger.debug("ChannelCall for {0} stopping".format(
                        type(self.call_object)
                    ))
                break

            if self.logger:
                self.logger.debug("ChannelCall calling {0}.{1}".format(
                    type(self.call_object),
                    call.method
                ))

            method = getattr(self.call_object, call.method)
            result = method(*call.args, **call.kwargs)

            if self.logger:
                self.logger.debug("ChannelCall returning {0}.{1} "
                                  "response".format(
                    type(self.call_object),
                    call.method
                ))

            self.out_queue.put(result)


class ProcessCallRelay(CallRelay):
    def __init__(self, logger=None):
        in_queue = MPQueue()
        out_queue = MPQueue()

        super(ProcessCallRelay, self).__init__(logger, in_queue, out_queue)


class ThreadCallRelay(CallRelay):
    def __init__(self, logger=None):
        in_queue = Queue()
        out_queue = Queue()

        super(ThreadCallRelay, self).__init__(logger, in_queue, out_queue)

