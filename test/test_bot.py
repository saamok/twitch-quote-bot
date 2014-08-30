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

    def test__get_spin_result(self):
        dbPath = os.path.join(testPath, '__test_bot_get_spin_result.sqlite')
        self._delete(dbPath)

        settings = Settings()
        settings.DATABASE_PATH = dbPath

        bot = Bot(settings, FakeWrapper, logger=nullLogger)
        bot._initialize_db()
        result = bot._get_spin_result("#tmp", "test")

        assert result["score"] == 0
        assert result["last_spin_time"] is None

    def test__update_spin_result(self):
        dbPath = os.path.join(testPath, '__test_bot_update_spin_result.sqlite')
        self._delete(dbPath)

        settings = Settings()
        settings.DATABASE_PATH = dbPath

        bot = Bot(settings, FakeWrapper, logger=nullLogger)
        bot._initialize_db()
        bot._update_spin_result("#tmp", "test", 1)
        result = bot._get_spin_result("#tmp", "test")

        assert result["score"] == 1
        assert result["last_spin_time"] > 0

        bot._update_spin_result("#tmp", "test", 2, False)
        result = bot._get_spin_result("#tmp", "test")

        assert result["score"] == 2
        assert result["last_spin_time"] > 0

        bot._update_spin_result("#tmp", "test2", -1351355)
        result = bot._get_spin_result("#tmp", "test2")

        assert result["score"] == -1351355
        assert result["last_spin_time"] > 0

        result = bot._get_spin_result("#tmp", "test")

        assert result["score"] == 2
        assert result["last_spin_time"] > 0

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

    def test__get_spin(self):
        settings = Settings()
        settings.SPIN_MIN = -1
        settings.SPIN_MAX = 1

        bot = Bot(settings, FakeWrapper, logger=nullLogger)
        result = bot._get_spin()

        assert result >= -1
        assert result <= 1

        settings.SPIN_MIN = 100
        settings.SPIN_MAX = 100

        bot = Bot(settings, FakeWrapper, logger=nullLogger)
        result = bot._get_spin()

        assert result == 100

    def test__is_spin_ok(self):
        settings = Settings()
        settings.SPIN_TIMEOUT = 60

        bot = Bot(settings, FakeWrapper, logger=nullLogger)
        result = bot._is_spin_ok(None)

        assert result is True

        result = bot._is_spin_ok(1, 30)

        assert result is False

        result = bot._is_spin_ok(1, 61)

        assert result is True



    def _delete(self, path):
        """Delete a file"""

        try:
            os.remove(path)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
