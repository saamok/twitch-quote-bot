import os
from .bot import Bot
from .ircwrapper import IRCWrapper
from .utils import log, set_log_file

import settings


if __name__ == "__main__":

    if settings.LOG_FILE:
        set_log_file(settings.LOG_FILE)

    # Set LUA_PATH environment variable so our Lua code can find the libraries
    os.environ["LUA_PATH"] = settings.LUA_PATH

    bot = Bot(settings, wrapper_class=IRCWrapper, logger=log)
    bot.run()
