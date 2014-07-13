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

        tmp = Bot(settings, FakeWrapper, logger=nullLogger)
        tmp._initialize_db()
        tmp._add_quote("foobar", "#tmp", ["test"])
        quote_id, quote = tmp._get_random_quote("#tmp")

        assert str(quote) == "test"

    def test__del_quote(self):
        dbPath = os.path.join(testPath, '__test_bot_del_quote.sqlite')
        self._delete(dbPath)

        settings = Settings()
        settings.DATABASE_PATH = dbPath

        tmp = Bot(settings, FakeWrapper, logger=nullLogger)
        tmp._initialize_db()
        tmp._add_quote("foobar", "#tmp", ["test"])
        tmp._add_quote("foobar", "#tmp", ["test2"])
        tmp._del_quote("foobar", "#tmp", [1])

        quote_id, quote = tmp._get_random_quote("#tmp")

        print(quote_id, quote)

        assert str(quote) == "test2"

    def test_get_random_quote(self):
        dbPath = os.path.join(testPath, '__test_bot_get_random_quote.sqlite')
        self._delete(dbPath)

        settings = Settings()
        settings.DATABASE_PATH = dbPath

        tmp = Bot(settings, FakeWrapper, logger=nullLogger)
        tmp._initialize_db()
        quote_id, quote = tmp._get_random_quote("#tmp")

        assert quote_id == None
        assert quote == None

    def test__query(self):
        dbPath = os.path.join(testPath, '__test_bot_query.sqlite')
        self._delete(dbPath)

        settings = Settings()
        settings.DATABASE_PATH = dbPath

        tmp = Bot(settings, FakeWrapper, logger=nullLogger)
        tmp._initialize_db()

        sql = """
        INSERT INTO quotes__tmp (quote) VALUES(?)
        """
        tmp._query(sql, ("test123",))

        sql = """
        SELECT quote FROM quotes__tmp WHERE id=?
        """
        (quote, ) = tmp._query(sql, (1,))

        assert str(quote) == "test123"

    def _delete(self, path):
        """Delete a file"""

        try:
            os.remove(path)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
