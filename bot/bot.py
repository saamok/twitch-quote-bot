import sqlite3
from random import randint
from irc.bot import SingleServerIRCBot


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

        self.db = sqlite3.connect(settings.DATABASE_PATH)
        self.cursor = self.db.cursor()

        self.quote_table = "quotes_{channel}"
        self.regulars_table = "regulars_{channel}"

    def run(self):
        """Run the bot until we want to stop"""

        self.logger.info("Starting bot...")

        self._initialize_db()

        self.logger.info("Starting IRC connection")
        self.ircWrapper.start()

    def irc_command(self, channel, nick, command, args):
        """Command being called via IRC"""

        self.logger.debug("Got command {0} from {1} in {2}, with args: "
                          "{3}".format(command, nick, channel, " ".join(args)))

        try:
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

        except:
            message = "{0}, whoah, something went wrong. Please try again " \
                      "later."
            self._message(channel, message.format(nick))
            self.logger.error("I caught a booboo .. waah!", exc_info=True)

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

    def _can_run_command(self, channel, nick, command):
        """Is this guy allowed to run the command in this channel?"""

        if self.ircWrapper.is_oper(channel, nick):
            # Mods can do whatever they want
            return True
        if command in ("addquote", "quote",):
            if self._is_regular(channel, nick):
                return True

        return False

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

    def _get_regulars_table(self, channel):
        """Get the table for regulars on this channel"""

        return self.regulars_table.format(channel=self._clean_channel(channel))

    def _get_quote_table(self, channel):
        """Get the table for quotes on this channel"""

        return self.quote_table.format(channel=self._clean_channel(channel))

    def _clean_channel(self, channel):
        """Clean a channel name for use in table names"""

        return channel.replace("#", "_")

    def _query(self, sql, args=None):
        retval = None

        keyword = sql.strip().split(" ")[0].lower()

        try:
            if args:
                self.cursor.execute(sql, args)
            else:
                self.cursor.execute(sql)

            if keyword == "select":
                retval = self.cursor.fetchone()
            else:
                self.db.commit()

        except:
            self.logger.error("Whoah, something went wrong when running the "
                              "query: {0}".format(sql), exc_info=True)
            raise

        return retval


class IRCWrapper(SingleServerIRCBot):
    """Convenient wrapper for the irc class methods"""

    def __init__(self, logger, bot=None, channelList=None, nickname=None,
                 server=None, password=None,
                 port=6667, commandPrefix='!'):

        self.bot = bot
        self.logger = logger
        self.channelList = channelList
        self.commandPrefix = commandPrefix

        serverList = []

        if password:
            self.logger.info("Connecting to {0}:{1} with password {2}".format(
                server, port, password
            ))
            serverList.append((server, port, password))
        else:
            self.logger.info("Connecting to {0}:{1} with no password".format(
                server, port
            ))
            serverList.append((server, port))

        super(IRCWrapper, self).__init__(
            server_list=serverList,
            nickname=nickname,
            realname=nickname,
            reconnection_interval=15,
        )

    # Public API

    def message(self, channel, message):
        """Send a message to the channel"""

        self.connection.privmsg(channel, message)

    def is_oper(self, channel, nick):
        """Check if the user is an operator/moderator in the channel"""

        return self.channels[channel].is_oper(nick)

    # "Private" methods

    def on_disconnect(self, connection, event):
        """Event handler for being disconnected from the server"""

        import pdb; pdb.set_trace()

        self.logger.warn("Got disconnected from server: {0}".format(
            repr(event)
        ))

    def on_welcome(self, connection, event):
        """Event handler for when we connect to the server"""

        self.logger.info("Connected to server, joining channels...")

        for channel in self.channelList:
            self.logger.info("Joining channel {0}".format(channel))
            connection.join(channel)

    def on_join(self, connection, event):
        """Event handler for when we join a channel"""

        channel = self._get_channel(event)
        self.logger.info("Joined {0}".format(channel))

    def on_pubmsg(self, connection, event):
        """Event handler for when there is a message on any channel"""

        text = self._get_text(event)
        channel = self._get_channel(event)

        self.logger.debug("Got line on {0}: {1}".format(channel, text))

        command, args = self._get_command(text)

        if command:
            nick = self._get_nick(event)

            self.bot.irc_command(channel, nick, command, args)

    def _get_channel(self, event):
        """Get the channel the event occurred on"""

        return event.target

    def _get_text(self, event):
        """Get the message text from an event"""

        return event.arguments[0]

    def _get_nick(self, event):
        """Get the nickname that created this event"""

        return event.source.nick

    def _get_command(self, text):
        """Get the command from a line of text"""

        if not text.startswith(self.commandPrefix):
            return None, text

        # Strip off the command prefix
        text = text[len(self.commandPrefix):].strip()

        # Take the first word, in lowercase
        parts = text.split(' ')
        command = parts[0].lower()
        args = parts[1:]

        return command, args
