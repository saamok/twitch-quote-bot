import os
import time
from threading import Thread
from .bot import Bot
from .ircwrapper import IRCWrapper
from .utils import log, set_log_file
from .utils import ThreadCallRelay

import settings


if __name__ == "__main__":

    if settings.LOG_FILE:
        set_log_file(settings.LOG_FILE)

    # Set LUA_PATH environment variable so our Lua code can find the libraries
    os.environ["LUA_PATH"] = settings.LUA_PATH

    wrapper = ThreadCallRelay()
    bot = Bot(settings, wrapper=wrapper, irc_wrapper=IRCWrapper, logger=log)
    wrapper.set_call_object(bot)

    def run():
        bot.run()

    thread = Thread(target=run)
    thread.daemon = True
    thread.start()

    try:
        while True:
            time.sleep(1)
    finally:
        wrapper.stop()