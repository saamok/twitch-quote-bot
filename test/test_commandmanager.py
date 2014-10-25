import os
import bot.commandmanager
from bot.chat import Chat
from unittest import TestCase
from mock import Mock


class FakeBot(object):
    settings = None

    def set_command(self, channel, command, want_user, user_level, code):
        pass


class CommandManagerTest(TestCase):
    def setUp(self):
        os.environ["LUA_PATH"] = "lua/lib/?.lua;lua/lib/?/?.lua"

    def test_functions(self):
        chat = Chat(None, None)
        chat.message = Mock()
        cm = bot.commandmanager.CommandManager("#tmp", FakeBot(), chat=chat)

        # Some test command definitions
        def_commands = [
            "-ul=user -a=value test_func return tonumber(value) + 1",
            "-ul=reg --args=value test_func2 return __chat__test_func(value)"
            " + 10",
            "--args=... test_args local s = 0; for k, v in ipairs("
            "arg) do s = s + tonumber(v); end; return s"
        ]

        for line in def_commands:
            cm.add_command(line.split(" "))

        retval = cm.run_command("username", "mod", "test_func2", ["10"],
                                threaded=False)
        assert retval == 21

        retval = cm.run_command(
            "username", "mod", "test_args", ["1", "2", "3"], threaded=False
        )
        assert retval == 6

    def test_simple_functions(self):
        chat = Chat(None, None)
        chat.message = Mock()
        cm = bot.commandmanager.CommandManager("#tmp", FakeBot(), chat=chat)

        # Some test command definitions
        def_commands = [
            "test_func Hello there, {user}",
            "-ul=reg test_func2 Hello, {0}",
        ]

        for line in def_commands:
            cm.add_simple_command(line.split(" "))

        retval = cm.run_command("username", "mod", "test_func", [],
                                threaded=False)
        assert retval == "Hello there, username"

        retval = cm.run_command(
            "username", "reg", "test_func2", ["target"], threaded=False
        )
        assert retval == "Hello, target"

        self.assertRaises(
            bot.commandmanager.CommandPermissionError,
            cm.run_command,
            "username",
            "user",
            "test_func2"
        )

    def test_want_user(self):
        chat = Chat(None, None)
        chat.message = Mock()
        cm = bot.commandmanager.CommandManager("#tmp", FakeBot(), chat=chat)

        # Some test command definitions
        line = "-w test return user"
        cm.add_command(line.split(" "))

        retval = cm.run_command("fakeuser", "mod", "test", threaded=False)
        assert retval == "fakeuser"

    def test_quoted(self):
        chat = Chat(None, None)
        chat.message = Mock()
        cm = bot.commandmanager.CommandManager("#tmp", FakeBot(), chat=chat)

        # Some test command definitions
        def_commands = [
            "-q -a=name,job test_quoted return name .. ': ' .. job",
            "-a=name,job test_not_quoted return name .. ': ' .. job",
        ]

        for line in def_commands:
            cm.add_command(line.split(" "))

        args = '"John Doe" "Car Salesman"'.split(" ")
        retval = cm.run_command("fakeuser", "mod", "test_quoted", args,
                                threaded=False)
        assert retval == "John Doe: Car Salesman"

        retval = cm.run_command("fakeuser", "mod", "test_not_quoted", args,
                                threaded=False)
        assert retval == '"John: Doe"'

    def test_cooldown(self):

        chat = Chat(None, None)
        chat.message = Mock()
        cm = bot.commandmanager.CommandManager("#tmp", FakeBot(), chat=chat)

        # Some test command definitions
        def_commands = [
            "-c=5 cd_test Cooldown test",
        ]

        for line in def_commands:
            cm.add_simple_command(line.split(" "))

        def run_cmd(timestamp):
            def _run():
                return cm.run_command(
                    "username", "mod", "cd_test", [], timestamp=timestamp,
                    threaded=False
                )

            return _run

        retval = run_cmd(1)()
        assert retval == "Cooldown test"

        self.assertRaises(
            bot.commandmanager.CommandCooldownError, run_cmd(2)
        )

        retval = run_cmd(6)()
        assert retval == "Cooldown test"

    def test_permissions(self):

        chat = Chat(None, None)
        chat.message = Mock()
        cm = bot.commandmanager.CommandManager("#tmp", FakeBot(),
                                               chat=chat)

        # Some test command definitions
        def_commands = [
            "-ul=owner owner_func return 0",
            "-ul=mod mod_func return 1",
            "-ul=reg reg_func return 2",
            "-ul=user user_func return 3"
        ]

        for line in def_commands:
            cm.add_command(line.split(" "))

        # owner_func

        self.assertRaises(
            bot.commandmanager.CommandPermissionError,
            cm.run_command,
            "username",
            "mod",
            "owner_func"
        )

        cm.run_command("username", "owner", "owner_func", threaded=False)
        chat.message.assert_called_with(0)

        # mod_func

        self.assertRaises(
            bot.commandmanager.CommandPermissionError,
            cm.run_command,
            "username",
            "reg",
            "mod_func"
        )

        cm.run_command("username", "mod", "mod_func", threaded=False)
        chat.message.assert_called_with(1)

        # reg_func

        self.assertRaises(
            bot.commandmanager.CommandPermissionError,
            cm.run_command,
            "username",
            "user",
            "reg_func"
        )

        cm.run_command("username", "reg", "reg_func", threaded=False)
        chat.message.assert_called_with(2)

        cm.run_command("username", "owner", "reg_func", threaded=False)
        chat.message.assert_called_with(2)

        # user_func

        cm.run_command("username", "user", "user_func", threaded=False)
        chat.message.assert_called_with(3)

    def test_unicode(self):
        chat = Chat(None, None)
        chat.message = Mock()
        cm = bot.commandmanager.CommandManager("#tmp", FakeBot(), chat=chat)

        line = u"test ヽ༼ຈل͜ຈ༽ﾉ AMENO ヽ༼ຈل͜ຈ༽ﾉ"
        cm.add_simple_command(line.split(" "))

        cm.run_command("username", "mod", "test", threaded=False)
        chat.message.assert_called_with(u"ヽ༼ຈل͜ຈ༽ﾉ AMENO ヽ༼ຈل͜ຈ༽ﾉ")
