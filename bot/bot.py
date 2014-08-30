from glob import glob
import json
import sqlite3
from random import randint
from .commandmanager import CommandManager, CommandPermissionError
from lupa import LuaError


class Bot(object):
    """The core bot logic"""

    def __init__(self, settings, wrapper_class, logger):
        self.settings = settings

        self.logger = logger

        self.ircWrapper = wrapper_class(
            logger,
            self,
            settings.CHANNEL_LIST,
            settings.USER,
            settings.HOST,
            settings.OAUTH_TOKEN,
            settings.PORT,
            settings.COMMAND_PREFIX
        )

        self.command_managers = {}

        self.db = sqlite3.connect(settings.DATABASE_PATH)
        self.cursor = self.db.cursor()

        self.quote_table = "quotes_{channel}"
        self.regulars_table = "regulars_{channel}"
        self.command_table = "commands_{channel}"
        self.data_table = "data_{channel}"

    def __del__(self):
        if self.ircWrapper:
            self.ircWrapper.stop()

    def run(self):
        """Run the bot until we want to stop"""

        self.logger.info("Starting bot...")

        self._initialize_db()

        self._initialize_command_managers()

        self.logger.info("Starting IRC connection")
        self.ircWrapper.start()

    def irc_command(self, channel, nick, command, args):
        """Command being called via IRC"""

        self.logger.debug("Got command {0} from {1} in {2}, with args: "
                          "{3}".format(command, nick, channel, " ".join(args)))

        try:
            if not self._is_core_command(command):
                cm = self.command_managers[channel]
                if cm.is_valid_command(command):
                    self._handle_custom_command(channel, nick, command, args)
                return

            if not self._can_run_command(channel, nick, command):
                self.logger.info("Command access denied")
                message = "{0}, sorry, but you are not allowed to use that " \
                          "command."
                self._message(channel, message.format(nick))
                return

            if command == "addquote":
                self._add_quote(nick, channel, args)
            elif command == "delquote":
                self._del_quote(nick, channel, args)
            elif command == "quote":
                self._show_quote(nick, channel, args)
            elif command == "reg":
                self._manage_regulars(nick, channel, args)
            elif command == "def":
                cm = self.command_managers[channel]
                command, user_level = cm.add_command(args)

                message = "{0}, added command {1} for user level {2}".format(
                    nick, command, user_level
                )
                self._message(channel, message)

        except:
            message = "{0}, whoah, something went wrong. Please try again " \
                      "later."
            self._message(channel, message.format(nick))
            self.logger.error("I caught a booboo .. waah!", exc_info=True)

    def set_command(self, channel, command, want_user, user_level, code):
        """Handler for saving commands from the command manager"""

        self._set_command(channel, command, want_user, user_level, code)

    def update_global_value(self, channel, key, value):
        """Set a global persistant value on the channel"""

        self._update_channel_data(channel, key, value)

    def _handle_custom_command(self, channel, nick, command, args):
        """Handle running custom commands from chat"""

        user_level = self._get_user_level(channel, nick)
        cm = self.command_managers[channel]

        try:
            result = cm.run_command(nick, user_level, command, args)
        except CommandPermissionError:
            result = "{0}, you don't have permissions to run that " \
                     "command".format(nick)
        except LuaError as e:
            result = "{0}, oops, got Lua error: {1}".format(
                nick, str(e)
            )

        self.logger.debug("Custom command {0} returned {1}".format(
            command, result
        ))

        self._message(channel, result)

    def _is_core_command(self, command):
        """Check if the command we got is actually a command we support"""

        return command in [
            "addquote",
            "delquote",
            "quote",
            "reg",
            "def"
        ]

    def _get_user_level(self, channel, user):
        """Figure out the user's level on the channel"""

        level = "user"

        if self._is_mod(channel, user):
            level = "mod"
        elif self._is_regular(channel, user):
            level = "reg"

        return level

    def _message(self, channel, message):
        """Send a message to a channel"""

        self.logger.debug("Sending message to {0}: {1}".format(
            channel, message
        ))

        self.ircWrapper.message(channel, message)

    def _add_quote(self, nick, channel, args):
        """Add a quote to the database"""

        quote = " ".join(args)
        if len(quote) == 0:
            self.logger.info("Got 0 length addquote call from {0} in "
                             "{1}?".format(nick, channel))

            message = "{0}, ehh .. you gave me no quote?"
            self.message(channel, message.format(nick))
            return

        sql = """
        INSERT INTO '{table}'
          (quote)
        VALUES
          (?);
        """.format(table=self._get_quote_table(channel))

        self._query(sql, (quote,))

        message = "{0}, New quote added."
        self._message(channel, message.format(nick))

        self.logger.info("Added quote for {0}: {1}".format(channel, quote))

    def _del_quote(self, nick, channel, args):
        """Remove a quote from the database"""

        if len(args) == 0:
            self.logger.info("Got 0 length delquote call from {0} in "
                             "{1}?".format(nick, channel))

            message = "{0}, ehh .. you gave me no quote ID?"
            self.message(channel, message.format(nick))
            return

        quote_id = args[0]

        sql = """
        DELETE FROM '{table}'
        WHERE id=?;
        """.format(table=self._get_quote_table(channel))

        self._query(sql, (quote_id,))

        message = "{0}, Quote removed."
        self._message(channel, message.format(nick))

        self.logger.info("Removed quote {0} for {1}".format(quote_id, channel))

    def _manage_regulars(self, nick, channel, args):
        """Manage regulars for a channel"""

        ok = True
        if len(args) != 2:
            ok = False

        action = args[0].lower()
        regular = args[1].lower()

        if not action in ('add', 'del'):
            ok = False

        if not ok:
            self.logger.warn("Manage regulars got invalid args?")
            message = "{0}, that doesn't look like a valid command?"
            self._message(channel, message.format(nick))

            return

        if action == 'add':
            if self._is_regular(channel, regular):
                self.logger.info(
                    "Trying to add {0} to {1} regulars, but they were "
                    "already one.".format(
                        regular, channel
                    )
                )
                message = "{0}, {1} is already a regular?"
                self._message(channel, message.format(nick, regular))
                return

            self._add_regular(channel, regular)
            message = "{0}, Added new regular: {1}"
            self._message(channel, message.format(nick, regular))
        elif action == 'del':
            if not self._is_regular(channel, regular):
                self.logger.info(
                    "Trying to remove {0} from {1} regulars, but they weren't "
                    "a regular there.".format(
                        regular, channel
                    )
                )
                message = "{0}, {1} is not a regular?"
                self._message(channel, message.format(nick, regular))
                return

            self._remove_regular(channel, regular)
            message = "{0}, Removed regular: {1}"
            self._message(channel, message.format(nick, regular))

    def _show_quote(self, nick, channel, args):
        """Show a quote on channel"""

        quote_id, quote = self._get_random_quote(channel)
        if quote:
            message = "Quote #{0}: {1}".format(quote_id, quote)
            self._message(channel, message)

            self.logger.info("Showed quote for channel {0}: {1}".format(
                channel, quote
            ))
        else:
            message = "No quotes in the database. Maybe you should add one?"
            self._message(channel, message)

            self.logger.info("No quotes for channel {0}".format(channel))

    def _get_random_quote(self, channel):
        max_id = self._get_max_id(self._get_quote_table(channel))

        if max_id is None:
            return None, None

        quote_id = randint(1, max_id)

        sql = """
        SELECT quote
        FROM {table}
        WHERE id >= ?
        LIMIT 1""".format(table=self._get_quote_table(channel))

        (quote, ) = self._query(sql, (quote_id,))

        return quote_id, str(quote)

    def _get_max_id(self, table):
        """Get the maximum ID on the given table"""

        sql = """
        SELECT MAX(id)
        FROM {table}
        """.format(table=table)

        (result, ) = self._query(sql)

        self.logger.debug("Max ID for {0} seems to be".format(table))

        return result

    def _initialize_db(self):
        """Make sure our database tables exist"""

        self.logger.debug("Initializing database")

        for channel in self.settings.CHANNEL_LIST:
            self.logger.debug("Creating tables for {0}".format(channel))
            # TODO: Convert to an .sql file
            sql = """
            CREATE TABLE IF NOT EXISTS {table}
            (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              quote TEXT
            )""".format(table=self._get_quote_table(channel))

            self._query(sql)

            sql = """
            CREATE TABLE IF NOT EXISTS {table}
            (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              nick TEXT
            )""".format(table=self._get_regulars_table(channel))

            self._query(sql)
            self._query("CREATE UNIQUE INDEX IF NOT EXISTS reg_nick on "
                        "{table} (nick)".format(
                table=self._get_regulars_table(channel)
            ))

            sql = """
            CREATE TABLE IF NOT EXISTS {table}
            (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              command TEXT,
              want_user BOOL,
              user_level TEXT,
              code TEXT
            )""".format(table=self._get_command_table(channel))

            self._query(sql)
            self._query("CREATE UNIQUE INDEX IF NOT EXISTS command on "
                        "{table} (command)"
                        .format(table=self._get_command_table(channel))
            )

            sql = """
            CREATE TABLE IF NOT EXISTS {table}
            (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              key TEXT,
              value TEXT
            )""".format(table=self._get_data_table(channel))

            self._query(sql)
            self._query("CREATE UNIQUE INDEX IF NOT EXISTS data_key on "
                        "{table} (key)"
                        .format(table=self._get_data_table(channel))
            )

    def _can_run_command(self, channel, nick, command):
        """Is this guy allowed to run the command in this channel?"""

        if self._is_mod(channel, nick):
            # Mods can do whatever they want
            return True
        elif command in ("addquote", "quote"):
            if self._is_regular(channel, nick):
                return True

        return False

    def _is_mod(self, channel, user):
        """Check if the given user is a mod on the given channel"""

        return self.ircWrapper.is_oper(channel, user)

    def _set_command(self, channel, command, want_user, user_level, code):
        """Save a command on the channel"""

        sql = """
        REPLACE INTO {table} (command, want_user, user_level, code)
        VALUES(?, ?, ?, ?)
        """.format(table=self._get_command_table(channel))

        self._query(sql, (command, want_user, user_level, code))

    def _load_commands(self, channel):
        """Load the commands available for this channel"""

        sql = """
        SELECT command, want_user, user_level, code
        FROM {table}
        """.format(table=self._get_command_table(channel))

        entries = self._query(sql, multiple_values=True)

        return entries

    def _is_regular(self, channel, nick):
        """Is this guy on the regulars list?"""

        sql = """
        SELECT *
        FROM {table}
        WHERE nick=?
        """.format(table=self._get_regulars_table(channel))

        entry = self._query(sql, (nick, ))
        self.logger.debug("Is regular: {0}".format(repr(entry)))

        if entry is None:
            self.logger.debug("{0} is NOT a regular for {1}".format(
                nick, channel
            ))
            return False

        self.logger.debug("{0} is a regular for {1}".format(
            nick, channel
        ))

        return True

    def _add_regular(self, channel, nick):
        """Add a new regular to channel"""

        sql = """
        INSERT INTO {table}
          (nick) VALUES (?);
        """.format(table=self._get_regulars_table(channel))

        self._query(sql, (nick, ))

        self.logger.info("Added regular {0} to {1}".format(nick, channel))

    def _remove_regular(self, channel, nick):
        """Remove a regular from the channel"""

        sql = """
        DELETE FROM {table}
        WHERE nick=?;
        """.format(table=self._get_regulars_table(channel))

        self._query(sql, (nick, ))

        self.logger.info("Removed regular {0} from {1}".format(nick, channel))

    def _update_channel_data(self, channel, key, value):
        """Update a single value for this channel's data"""

        sql = """
        REPLACE INTO {table} (key, value)
        VALUES(?, ?)
        """.format(table=self._get_data_table(channel))

        json_value = json.dumps(value)

        self._query(sql, (key, json_value))


    def _load_channel_data(self, channel):
        """Load stored channel data"""

        sql = """
        SELECT key, value
        FROM {table}
        """.format(table=self._get_data_table(channel))

        entries = self._query(sql, multiple_values=True)

        data = {}
        for entry in entries:
            data[entry[0]] = json.loads(entry[1])

        return data

    def _get_regulars_table(self, channel):
        """Get the table for regulars on this channel"""

        return self.regulars_table.format(channel=self._clean_channel(channel))

    def _get_quote_table(self, channel):
        """Get the table for quotes on this channel"""

        return self.quote_table.format(channel=self._clean_channel(channel))

    def _get_command_table(self, channel):
        """Get the table for commands on this channel"""

        return self.command_table.format(channel=self._clean_channel(channel))

    def _get_data_table(self, channel):
        """Get the table for data on this channel"""

        return self.data_table.format(channel=self._clean_channel(channel))

    def _clean_channel(self, channel):
        """Clean a channel name for use in table names"""

        return channel.replace("#", "_")

    def _initialize_command_managers(self):
        """Initialize our channel command managers"""

        lua_files = self._find_lua_files()

        for channel in self.settings.CHANNEL_LIST:
            channel_data = self._load_channel_data(channel)
            cm = CommandManager(
                channel,
                self,
                channel_data,
                self.logger
            )

            for filename in lua_files:
                with open(filename, 'r') as handle:
                    code = handle.read()
                    self.logger.debug("Loading Lua for {0} from {1}".format(
                        channel, filename
                    ))
                    cm.load_lua(code)

            commands = self._load_commands(channel)

            for command_data in commands:
                cm.load_command(*command_data, set=False)

            self.command_managers[channel] = cm

    def _find_lua_files(self):
        return glob(self.settings.LUA_INCLUDE_GLOB)

    def _query(self, sql, args=None, multiple_values=False):
        """Run a query against our sqlite database"""

        retval = None

        keyword = sql.strip().split(" ")[0].lower()

        try:
            if args:
                self.cursor.execute(sql, args)
            else:
                self.cursor.execute(sql)

            if keyword == "select":
                if multiple_values:
                    retval = self.cursor.fetchall()
                else:
                    retval = self.cursor.fetchone()
            else:
                self.db.commit()

        except:
            self.logger.error("Whoah, something went wrong when running the "
                              "query: {0}".format(sql), exc_info=True)
            raise

        return retval
