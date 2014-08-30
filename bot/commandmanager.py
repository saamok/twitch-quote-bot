from time import time
from .utils import human_readable_time
import lupa
import argparse


class CommandPermissionError(BaseException):
    pass


class DataSource(object):
    def __init__(self, channel, bot, data=None):
        if not data:
            data = {}

        self.channel = channel
        self.bot = bot
        self.data = data

    def __getitem__(self, item):
        return self.__dict__["data"][item]

    def __setitem__(self, key, value):
        self.__dict__["data"][key] = value
        self.bot.update_global_value(self.channel, key, value)


class CommandManager(object):
    def __init__(self, channel, bot, data=None, logger=None):
        self.channel = channel
        self.bot = bot
        self.logger = logger
        self.commands = {}
        self.datasource = DataSource(channel, bot, data)

        self.func_template = """
        function {func_name}({args})
            {func_body}
        end
        """

        self.call_template = """
        function(...)
            return {func_name}(unpack(arg))
        end
        """

        self.lua = lupa.LuaRuntime(unpack_returned_tuples=False)
        self._inject_globals()

    def add_command(self, args):
        """Add a new function to the command manager"""

        command, want_user, user_level, code = self._parse_func(args)

        self.load_command(command, want_user, user_level, code)

        return command, user_level

    def is_valid_command(self, command):
        """Check if the given command is known to us"""

        return command in self.commands

    def load_command(self, command, want_user, user_level, code, set=True):
        """Load a previously persisted command"""

        if self.logger:
            self.logger.debug("Loading command {0} with user level {1} and "
                              "code: {2}".format(
                command, user_level, code
            ))

        self.commands[command] = {
            "want_user": want_user,
            "user_level": user_level,
            "code": code
        }

        if set:
            self.bot.set_command(
                self.channel, command, want_user, user_level, code
            )

        self.load_lua(code)

    def run_command(self, username, user_level, command, args=None):
        """Run a command with the given args"""

        if not self._can_run_command(user_level, command):
            raise CommandPermissionError("User does not have permission to "
                                         "run this command")

        if args is None:
            args = []

        code = self.call_template.format(func_name=command)
        lua_func = self.lua.eval(code)

        if self.commands[command]["want_user"]:
            args.insert(0, username)

        retval = lua_func(*args)

        return retval

    def load_lua(self, code):
        """Load Lua code in the runtime"""

        self.lua.execute(code)

    def _parse_func(self, args):
        """Parse arguments into a function definition"""

        parser = argparse.ArgumentParser()
        parser.add_argument("-ul", "--user_level", default="mod")
        parser.add_argument("-a", "--args", default="")
        parser.add_argument("-w", "--want_user", action="store_true",
                            default=False)
        parser.add_argument("func_name")
        parser.add_argument("func_body", nargs='*')
        options = parser.parse_args(args)

        # Rebuild code

        if options.want_user:
            new_args = "user"
            if len(options.args) > 0:
                new_args += ","

            options.args = new_args + options.args

        code = self.func_template.format(
            func_name=options.func_name,
            args=options.args,
            func_body=" ".join(options.func_body)
        )

        return options.func_name, options.want_user, options.user_level, code

    def _level_name_to_number(self, name):
        levels = [
            "user",
            "reg",
            "mod",
            "owner"
        ]

        if not name in levels:
            raise ValueError("{0} is not a valid user level".format(name))

        return levels.index(name)

    def _can_run_command(self, user_level, command):
        """Permission check for commands"""

        need_level = self._level_name_to_number(
            self.commands[command]["user_level"]
        )

        got_level = self._level_name_to_number(user_level)

        return got_level >= need_level

    def _inject_globals(self):
        injector = self.lua.eval("""
            function (key, value)
                _G[key] = value
            end
        """)

        injector("datasource", self.datasource)
        injector("human_readable_time", human_readable_time)
        injector("settings", self.bot.settings)
