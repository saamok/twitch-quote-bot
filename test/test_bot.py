import logging
import inspect
import os
import errno
from unittest import TestCase
from bot.bot import Bot


nullLogger = logging.getLogger('null')
nullLogger.setLevel(999)

testPath = os.path.dirname(
    os.path.abspath(
        inspect.getfile(inspect.currentframe())
    )
)


class FakeWrapper(object):
    def __init__(self, *args):
        pass

    def stop(self):
        pass

    def message(self, *args):
        pass


class Settings(object):
    CHANNEL_LIST = ["#tmp"]
    USER = ""
    HOST = ""
    OAUTH_TOKEN = ""
    PORT = ""
    COMMAND_PREFIX = ""
    DATABASE_PATH = ""


class BotTest(TestCase):
    """Make sure the Bot class seems sane"""

    def test_irc_command(self):
        pass

    def test__add_quote(self):
        dbPath = os.path.join(testPath, '__test_bot_add_quote.sqlite')
        self._delete(dbPath)

        settings = Settings()
        settings.DATABASE_PATH = dbPath

        bot = Bot(settings, FakeWrapper, logger=nullLogger)
        bot._initialize_db()
        bot._add_quote("foobar", "#tmp", ["test"])
        quote_id, quote = bot._get_random_quote("#tmp")

        assert str(quote) == "test"

    def test__del_quote(self):
        dbPath = os.path.join(testPath, '__test_bot_del_quote.sqlite')
        self._delete(dbPath)

        settings = Settings()
        settings.DATABASE_PATH = dbPath

        bot = Bot(settings, FakeWrapper, logger=nullLogger)
        bot._initialize_db()
        bot._add_quote("foobar", "#tmp", ["test"])
        bot._add_quote("foobar", "#tmp", ["test2"])
        bot._del_quote("foobar", "#tmp", [1])

        quote_id, quote = bot._get_random_quote("#tmp")

        print(quote_id, quote)

        assert str(quote) == "test2"

    def test_get_random_quote(self):
        dbPath = os.path.join(testPath, '__test_bot_get_random_quote.sqlite')
        self._delete(dbPath)

        settings = Settings()
        settings.DATABASE_PATH = dbPath

        bot = Bot(settings, FakeWrapper, logger=nullLogger)
        bot._initialize_db()
        quote_id, quote = bot._get_random_quote("#tmp")

        assert quote_id is None
        assert quote is None

    def test_update_global_value(self):
        dbPath = os.path.join(testPath, '__test_bot_update_global_value.sqlite')
        self._delete(dbPath)

        settings = Settings()
        settings.DATABASE_PATH = dbPath

        bot = Bot(settings, FakeWrapper, logger=nullLogger)
        bot._initialize_db()
        bot.update_global_value("#tmp", "test", {"key1": "value1"})

        data = bot._load_channel_data("#tmp")

        assert data["test"]["key1"] == "value1"

    def test__query(self):
        dbPath = os.path.join(testPath, '__test_bot_query.sqlite')
        self._delete(dbPath)

        settings = Settings()
        settings.DATABASE_PATH = dbPath

        bot = Bot(settings, FakeWrapper, logger=nullLogger)
        bot._initialize_db()

        sql = """
        INSERT INTO quotes__tmp (quote) VALUES(?)
        """
        bot._query(sql, ("test123",))

        sql = """
        SELECT quote FROM quotes__tmp WHERE id=?
        """
        (quote, ) = bot._query(sql, (1,))

        assert str(quote) == "test123"

    def _delete(self, path):
        """Delete a file"""

        try:
            os.remove(path)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
