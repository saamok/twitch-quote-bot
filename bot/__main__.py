from .bot import Bot
from .ircwrapper import IRCWrapper
from .utils import log, set_log_file

import settings


if __name__ == "__main__":

    if settings.LOG_FILE:
        set_log_file(settings.LOG_FILE)

    bot = Bot(settings, wrapper_class=IRCWrapper, logger=log)
    bot.run()
