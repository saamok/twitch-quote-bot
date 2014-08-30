import bot.commandmanager
from unittest import TestCase


class FakeBot(object):
    def set_command(self, channel, name, user_level, code):
        pass


class UtilsTest(TestCase):
    def test_functions(self):
        cm = bot.commandmanager.CommandManager("#tmp", FakeBot())

        # Some test command definitions
        def_commands = [
            "-ul=user -a=value test_func return tonumber(value) + 1",
            "-ul=reg --args=value test_func2 return test_func(value) + 10",
            "--args=... test_args local s = 0; for k, v in ipairs("
            "arg) do s = s + tonumber(v); end; return s"
        ]

        for line in def_commands:
            cm.add_command(line.split(" "))

        retval = cm.run_command("mod", "test_func2", ["10"])
        assert retval == 21

        retval = cm.run_command("mod", "test_args", ["1", "2", "3"])
        assert retval == 6

    def test_permissions(self):

        cm = bot.commandmanager.CommandManager("#tmp", FakeBot())

        # Some test command definitions
        def_commands = [
            "-ul=mod mod_func return 1",
            "-ul=reg reg_func return 2",
            "-ul=user user_func return 3"
        ]

        for line in def_commands:
            cm.add_command(line.split(" "))

        # mod_func

        self.assertRaises(
            bot.commandmanager.CommandPermissionError,
            cm.run_command,
            "reg",
            "mod_func"
        )

        retval = cm.run_command("mod", "mod_func")
        assert retval == 1

        # reg_func

        self.assertRaises(
            bot.commandmanager.CommandPermissionError,
            cm.run_command,
            "user",
            "reg_func"
        )

        retval = cm.run_command("reg", "reg_func")
        assert retval == 2

        retval = cm.run_command("owner", "reg_func")
        assert retval == 2

        # user_func

        retval = cm.run_command("user", "user_func")
        assert retval == 3

