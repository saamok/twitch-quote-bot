from time import time
from glob import glob
import sqlite3
from random import randint
from .utils import human_readable_time
from .commandmanager import CommandManager


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
        self.spin_table = "spins_{channel}"
        self.command_table = "commands_{channel}"

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
            elif command == "spin":
                self._spin(nick, channel, args)
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

    def set_command(self, channel, command, user_level, code):
        """Handler for saving commands from the command manager"""

        self._set_command(channel, command, user_level, code)

    def _handle_custom_command(self, channel, nick, command, args):
        """Handle running custom commands from chat"""

        user_level = self._get_user_level(channel, nick)
        cm = self.command_managers[channel]

        try:
            result = cm.run_command(user_level, command, args)
        except CommandPermissionError:
            result = "you don't have permissions to run that command"

        message = "{0}, {1}".format(
            nick, result
        )

        self._message(channel, message)

    def _is_core_command(self, command):
        """Check if the command we got is actually a command we support"""

        return command in [
            "addquote",
            "delquote",
            "quote",
            "spin",
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

    def _spin(self, nick, channel, args):
        """Spin the wheel of fortune"""

        previous = self._get_spin_result(channel, nick)
        if previous["last_spin_time"] is None:
            new = True
        else:
            new = False

        spin_wait = self._get_spin_wait(previous["last_spin_time"])
        if spin_wait is not None:
            wait_time = human_readable_time(spin_wait)
            message = "{0}, you need to chillax, try again in {1}..."
            self._message(channel, message.format(nick, wait_time))
            return

        spin = self._get_spin()
        total_score = spin + previous["score"]

        self._update_spin_result(channel, nick, total_score, new)

        message = "{0}, the wheel of fortune has granted you {1} point(s)! " \
                  "You now have a total of {2} point(s)."

        self._message(channel, message.format(
            nick, spin, total_score
        ))

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
              nick TEXT,
              score INTEGER,
              last_spin_time INTEGER
            )""".format(table=self._get_spin_table(channel))

            self._query(sql)
            self._query("CREATE UNIQUE INDEX IF NOT EXISTS spin_nick on "
                        "{table} (nick)".format(
                table=self._get_spin_table(channel)
            ))

            sql = """
            CREATE TABLE IF NOT EXISTS {table}
            (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              command TEXT,
              user_level TEXT,
              code TEXT
            )""".format(table=self._get_command_table(channel))

            self._query(sql)
            self._query("CREATE UNIQUE INDEX IF NOT EXISTS command on "
                        "{table} (command)"
                        .format(table=self._get_command_table(channel))
            )

    def _can_run_command(self, channel, nick, command):
        """Is this guy allowed to run the command in this channel?"""

        if self._is_mod(channel, nick):
            # Mods can do whatever they want
            return True
        elif command in ("addquote", "quote"):
            if self._is_regular(channel, nick):
                return True
        elif command in ("spin", ):
            # Public commands
            return True

        return False

    def _is_mod(self, channel, user):
        """Check if the given user is a mod on the given channel"""

        return self.ircWrapper.is_oper(channel, user)

    def _set_command(self, channel, command, user_level, code):
        """Save a command on the channel"""

        sql = """
        REPLACE INTO {table} (command, user_level, code)
        VALUES(?, ?, ?)
        """.format(table=self._get_command_table(channel))

        self._query(sql, (command, user_level, code))

    def _load_commands(self, channel):
        """Load the commands available for this channel"""

        sql = """
        SELECT command, user_level, code
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

    def _get_spin_result(self, channel, nick):
        """Get any previous spin result data for this user"""

        sql = """
        SELECT score, last_spin_time
        FROM {table}
        WHERE nick=?
        """.format(table=self._get_spin_table(channel))

        result = self._query(sql, (nick, ))
        self.logger.debug("Spin result for {0}: {1}".format(
            nick, repr(result)
        ))

        if result is None:
            self.logger.debug("{0} has no previous spin result for {1}".format(
                nick, channel
            ))

            return {
                "score": 0,
                "last_spin_time": None
            }

        (score, last_spin_time) = result

        self.logger.debug("{0} previous spin result on {1} was {2} at {3}"
                          "".format(
            nick, channel, score, last_spin_time
        ))

        return {
            "score": score,
            "last_spin_time": last_spin_time
        }

    def _update_spin_result(self, channel, nick, score, new=True):
        """Write a spin result for this user"""

        last_spin_time = int(time())

        if new:
            sql = """
            INSERT INTO {table} (nick, score, last_spin_time)
            VALUES(?, ?, ?)
            """.format(table=self._get_spin_table(channel))

            self._query(sql, (nick, score, last_spin_time))
        else:
            sql = """
            UPDATE {table}
            SET score=?,
                last_spin_time=?
            WHERE nick=?
            """.format(table=self._get_spin_table(channel))

            self._query(sql, (score, last_spin_time, nick))

        self.logger.info("Updated {0} score on {1} to {2} at {3}".format(
            nick, channel, score, last_spin_time
        ))

    def _get_regulars_table(self, channel):
        """Get the table for regulars on this channel"""

        return self.regulars_table.format(channel=self._clean_channel(channel))

    def _get_spin_table(self, channel):
        """Get the table for spin results on this channel"""

        return self.spin_table.format(channel=self._clean_channel(channel))

    def _get_quote_table(self, channel):
        """Get the table for quotes on this channel"""

        return self.quote_table.format(channel=self._clean_channel(channel))

    def _get_command_table(self, channel):
        """Get the table for commands on this channel"""

        return self.command_table.format(channel=self._clean_channel(channel))

    def _clean_channel(self, channel):
        """Clean a channel name for use in table names"""

        return channel.replace("#", "_")

    def _get_spin_wait(self, last_spin_time, current_time=None):
        """Check if it's ok to spin right now"""

        if last_spin_time is None:
            return None

        if current_time is None:
            current_time = int(time())

        allow_spin_since = last_spin_time + self.settings.SPIN_TIMEOUT

        if allow_spin_since <= current_time:
            return None
        else:
            return allow_spin_since - current_time

    def _get_spin(self):
        """Get a new spin score"""

        return randint(self.settings.SPIN_MIN, self.settings.SPIN_MAX)

    def _initialize_command_managers(self):
        """Initialize our channel command managers"""

        lua_files = self._find_lua_files()

        for channel in self.settings.CHANNEL_LIST:
            cm = CommandManager(
                channel,
                self,
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
