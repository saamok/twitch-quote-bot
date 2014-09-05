import logging
from unittest import TestCase
from bot.ircwrapper import IRCWrapper
from irc.bot import Channel


nullLogger = logging.getLogger('null')
nullLogger.setLevel(999)


class IRCWrapperTest(TestCase):
    """Make sure the IRCWrapper class seems sane"""

    def test_is_oper(self):
        tmp = IRCWrapper(nullLogger)
        tmp.channels["#tmp"] = Channel()
        tmp.channels["#tmp"].operdict["foobar"] = True

        assert tmp.is_oper("#tmp", "foobar") is True
        assert tmp.is_oper("#tmp", "quux") is False

    def test_on_welcome(self):
        expected = ["#foo", "#bar"]
        joinList = []

        class FakeConnection(object):
            def join(self, channel):
                joinList.append(channel)

        tmp = IRCWrapper(nullLogger, channelList=expected)
        tmp.on_welcome(FakeConnection(), None)

        self.assertEqual(joinList, expected)

    def test_on_join(self):
        class Event(object):
            target = "#tmp"

        tmp = IRCWrapper(nullLogger)
        tmp.on_join(None, Event())

        # Just making sure this does not crash
        assert True

    def test_on_pubmsg(self):
        class EventSource(object):
            def __init__(self, nick=""):
                self.nick = nick

        class Event(object):
            def __init__(self, channel="", nick="", text=""):
                self.arguments = [text]
                self.target = channel
                self.source = EventSource(nick)

        class FakeSettings(object):
            QUEUE_DELAY = 1

        class FakeBot(object):
            data = None

            def irc_command(self, *args):
                self.data = args

        bot = FakeBot()

        tmp = IRCWrapper(nullLogger, bot, FakeSettings())
        tmp.on_pubmsg(None, Event(
            "#tmp",
            "foobar",
            "Hello, world! I am a traveler looking for safety!"
        ))

        assert bot.data is None

        tmp.on_pubmsg(None, Event(
            "#tmp",
            "foobar",
            "!hello can you hear me?"
        ))

        expected = (
            "#tmp",
            "foobar",
            "hello",
            ["can", "you", "hear", "me?"],
        )

        self.assertEqual(bot.data, expected)

        tmp = IRCWrapper(
            nullLogger, bot, FakeSettings(), commandPrefix="Hello, world!"
        )
        tmp.on_pubmsg(None, Event(
            "#tmp",
            "foobar",
            "Hello, world! I am a traveler looking for safety!"
        ))

        expected = (
            "#tmp",
            "foobar",
            "i",
            ["am", "a", "traveler", "looking", "for", "safety!"]
        )

        self.assertEqual(bot.data, expected)

    def test__get_command(self):
        text = "!test command"

        tmp = IRCWrapper(nullLogger, commandPrefix="!")
        command, args = tmp._get_command(text)

        assert command == "test"
        self.assertEqual(args, ["command"])

        text = "#testing rare command prefix... here's the args"

        tmp = IRCWrapper(nullLogger, commandPrefix="#testing rare command "
                                                   "prefix")
        command, args = tmp._get_command(text)

        assert command == "..."
        self.assertEqual(args, ["here's", "the", "args"])

        # Just making sure this does not crash
        assert True
