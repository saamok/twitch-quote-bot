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
            "-ul=reg --args=value test_func2 return test_func(value) + 10",
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

    def test_want_user(self):
        chat = Chat(None, None)
        chat.message = Mock()
        cm = bot.commandmanager.CommandManager("#tmp", FakeBot(), chat=chat)

        # Some test command definitions
        line = "-w test return user"
        cm.add_command(line.split(" "))

        retval = cm.run_command("fakeuser", "mod", "test", threaded=False)
        assert retval == "fakeuser"

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
