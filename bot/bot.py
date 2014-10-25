"""
The main bot logic module
"""

from datetime import datetime
from glob import glob
import json
from lupa import LuaError
from .commandmanager import CommandManager, CommandPermissionError, \
    CommandCooldownError
from .database import Database
from .utils import ThreadCallRelay, human_readable_time, ArgumentParser
from .blacklist import BlacklistManager


class Bot(object):
    """A bot instance"""

    def __init__(self, settings=None, wrapper=None, irc_wrapper=None,
                 logger=None, wrap_irc=True):
        self.settings = settings
        self.wrapper = wrapper
        self.logger = logger

        if irc_wrapper:
            iw = irc_wrapper(
                logger,
                self.wrapper,
                settings,
                settings.CHANNEL_LIST,
                settings.USER,
                settings.HOST,
                settings.OAUTH_TOKEN,
                settings.PORT,
                settings.COMMAND_PREFIX
            )

            if wrap_irc:
                self.ircWrapper = ThreadCallRelay()
                self.ircWrapper.set_call_object(iw)
                iw.set_call_relay(self.ircWrapper)
            else:
                self.ircWrapper = iw
        else:
            self.ircWrapper = None

        self.command_managers = {}
        self.blacklist_managers = {}
        self.channel_models = {}
        self.db = None

    #
    # Public API
    #

    def run(self):
        """
        Run the bot until we want to stop
        :return: None
        """

        self.logger.info(u"Starting bot...")

        self._initialize_models()

        self._initialize_command_managers()

        self._initialize_blacklists()

        self.logger.info(u"Starting IRC connection")
        self.ircWrapper.start()

        # Run until we want to exit
        self.wrapper.loop()

        self._stop()

    def _stop(self):
        """
        Stop everything we're doing

        :return:
        """
        if self.ircWrapper:
            self.ircWrapper.stop()

        for key in self.command_managers:
            self.command_managers[key].stop_timers()


    def get_settings(self):
        """
        Get the bot settings, needed due to ThreadCallRelay

        :return:
        """

        return self.settings

    def get_irc(self):
        """
        Get the IRC wrapper object

        :return:
        """

        return self.ircWrapper

    def chat_message(self, channel, nick, text, timestamp):
        """
        Process a non-command line from the chat

        :param channel: The channel where the command was issued on
        :param nick: The nick of the user that issued the command
        :param text: The text content of the message
        :param timestamp: The unixtime for when the event happened
        :return:
        """

        user_level = self._get_user_level(channel, nick)
        if user_level not in ("mod", "owner"):
            mgr = self.blacklist_managers[channel]
            res, rule_id, ban_time = mgr.is_blacklisted(text)
            if res:
                self.logger.info(
                    u"{nick} will be timed out for {time} due to blacklist "
                    u"rule #{id}".format(
                        nick=nick,
                        time=human_readable_time(ban_time),
                        id=rule_id
                    )
                )
                self.timeout(channel, nick, ban_time)

                message = u"{nick}, you triggered blacklist rule #{id}, " \
                          u"you were timed out for {time}".format(
                              nick=nick,
                              id=rule_id,
                              time=human_readable_time(ban_time)
                )

                self._message(channel, message)


    def irc_command(self, channel, nick, command, args, timestamp):
        """
        Process a command from the chat

        :param channel: The channel where the command was issued on
        :param nick: The nick of the user that issued the command
        :param command: The command issued
        :param args: All the words on the line after the command
        :param timestamp: The unixtime for when the event happened
        :return: If this was a valid command that was executed
        """

        try:
            self.logger.debug(u"Got command {0} from {1} in {2}, with args: "
                              u"{3}".format(command, nick, channel,
                                            " ".join(args)))

            if not self._is_core_command(command):
                cm = self.command_managers[channel]
                if cm.is_valid_command(command):
                    self._handle_custom_command(
                        channel, nick, command, args, timestamp
                    )
                return False

            if not self._is_allowed_to_run_command(channel, nick, command):
                self.logger.info(u"Command access denied")
                message = u"{0}, sorry, but you are not allowed to use that " \
                          u"command."
                self._message(channel, message.format(nick))
                return False

            if command == u"addquote":
                self._add_quote(channel, nick, args)
            elif command == u"delquote":
                self._del_quote(channel, nick, args)
            elif command == u"quote":
                self._show_quote(channel, nick, args)
            elif command == u"reg":
                self._manage_regulars(channel, nick, args)
            elif command == u"def" or command == u"com":
                cm = self.command_managers[channel]

                if command == u"def":
                    added, channel, command, flags, user_level, code = \
                        cm.add_command(
                            args
                        )
                else:
                    added, channel, command, flags, user_level, code = \
                        cm.add_simple_command(
                            args
                        )

                if added:
                    message = u"{0}, added command {1} for user level " \
                              u"{2}".format(
                        nick, command, user_level
                    )
                else:
                    message = u"{0}, removed command {1}".format(
                        nick, command, user_level
                    )

                self.set_command(
                    channel, command, flags, user_level, code
                )

                self._message(channel, message)
            elif command == u"blacklist":
                message = self._add_to_blacklist(channel, nick, args)
                self._message(channel, message)
            elif command == u"whitelist":
                message = self._add_to_whitelist(channel, nick, args)
                self._message(channel, message)
            elif command == u"unblacklist":
                message = self._remove_from_blacklist(channel, nick, args)
                self._message(channel, message)
            elif command == u"unwhitelist":
                message = self._remove_from_whitelist(channel, nick, args)
                self._message(channel, message)

            return True

        except BaseException as e:
            message = u"{0}, {1} error: {2}"
            exception_text = str(e)
            exception_text = exception_text.replace(u"<", "")
            exception_text = exception_text.replace(u">", "")

            self._message(channel, message.format(
                nick, e.__class__.__name__, exception_text
            ))
            self.logger.error(u"I caught a booboo .. waah!", exc_info=True)

        return False

    def set_command(self, channel, command, flags, user_level, code):
        """
        Save a new custom command or update existing one in the database

        :param channel: The channel the command is for
        :param command: What is the command called
        :param flags: Command flags
        :param user_level: The minimum user level to run the command
        :param code: The Lua code for the custom command
        :return: None
        """

        self._set_command(channel, command, flags, user_level, code)

    def update_global_value(self, channel, key, value):
        """
        Set a global persistent value on the channel

        :param channel: The channel the value is for
        :param key: The key for the value
        :param value: The value to store
        :return: None
        """

        self._update_channel_data(channel, key, value)

    def timeout(self, channel, nick, seconds):
        """
        Timeout the given user for the given amount of seconds
        :param channel:
        :param nick:
        :param seconds:
        :return:
        """

        message = ".timeout {nick} {seconds}".format(
            nick=nick, seconds=seconds
        )

        self._message(channel, message)

    #
    # Internal API
    #

    def _message(self, channel, message):
        """
        Deliver a message to the channel

        :param channel: The channel the message is to be delivered on
        :param message: The message text
        :return: None
        """

        self.logger.debug(u"Sending message to {0}: {1}".format(
            channel, message
        ))

        self.ircWrapper.message(channel, message)

    def _is_core_command(self, command):
        """
        Check if the given command is implemented in the "core" instead of
        e.g. being a custom one.

        :param command: The name of the command
        :return: True or False

        >>> from bot.bot import Bot
        >>> b = Bot()
        >>> b._is_core_command(u"def")
        True
        >>> b._is_core_command(u"get_fucked")
        False
        """

        return command in [
            u"addquote",
            u"delquote",
            u"blacklist",
            u"whitelist",
            u"unblacklist",
            u"unwhitelist",
            u"quote",
            u"reg",
            u"def",
            u"com"
        ]

    def _get_user_level(self, channel, nick):
        """
        Determine the nick's user level on the channel

        :param channel: Which channel
        :param nick: Whose user level
        :return: String "user", "reg", "mod", or "owner"
        """

        level = "user"

        if self._is_owner(nick):
            level = "owner"
        elif self._is_mod(channel, nick):
            level = "mod"
        elif self._is_regular(channel, nick):
            level = "reg"

        return level

    def _is_allowed_to_run_command(self, channel, nick, command):
        """
        Check if the given user has the permissions to run the given core
        command.

        :param channel: The channel the command was run on
        :param nick: Who is running the command
        :param command: The command being run
        :return: True or False
        """

        user_level = self._get_user_level(channel, nick)

        if user_level in ("mod", "owner"):
            # Mods and owners can run any and all core commands
            return True
        elif command in (u"addquote", u"delquote", u"quote"):
            if user_level == "reg":
                return True

        return False

    def _is_mod(self, channel, nick):
        """
        Check if the given nick is a moderator on the given channel

        :param channel: The name of the channel
        :param nick: The nick
        :return: True of False
        """

        return self.ircWrapper.is_oper(channel, nick)

    def _is_regular(self, channel, nick):
        """
        Check if the given nick is a regular on the given channel

        :param channel: The name of the channel
        :param nick: The nick
        :return: True of False
        """

        model = self._get_model(channel, "regulars")
        return model.filter(nick=nick).exists()

    def _is_owner(self, nick):
        """
        Check if the given nick belongs to a bot owner

        :param nick: The nick
        :return: True or False
        """

        return nick in self.settings.OWNER_USERS

    #
    # Chat commands
    #

    def _handle_custom_command(self, channel, nick, command, args, timestamp):
        """
        Handle execution of custom commands triggered via chat

        :param channel: The channel the command was triggered on
        :param nick: The nick that triggered it
        :param command: The command to be triggered
        :param args: The words on the line after the command
        :param timestamp: The unixtime for when the event happened
        :return: None
        """

        user_level = self._get_user_level(channel, nick)
        cm = self.command_managers[channel]

        message = None

        try:
            cm.run_command(nick, user_level, command, args, timestamp)
        except CommandPermissionError:
            message = u"{0}, you don't have permissions to run that " \
                      u"command".format(nick)
        except CommandCooldownError:
            self.logger.debug(u"Ignoring call to {0} due to cooldown".format(
                command
            ))
        except LuaError as e:
            message = u"{0}, oops, got Lua error: {1}".format(
                nick, str(e)
            )

        if message:
            self._message(channel, message)

    def _manage_regulars(self, channel, nick, args):
        """
        Handler for the "reg" -command, allows management of regulars

        :param channel: The channel the command was triggered on
        :param nick: The nick that triggered it
        :param args: The words on the line after the command
        :return: None
        """

        ok = True
        if len(args) != 2:
            ok = False

        action = args[0].lower()
        regular = args[1].lower()

        if not action in (u'add', u'del'):
            ok = False

        if not ok:
            self.logger.warn(u"Manage regulars got invalid args?")
            message = u"{0}, that doesn't look like a valid command?"
            self._message(channel, message.format(nick))

            return

        if action == u'add':
            if self._is_regular(channel, regular):
                self.logger.info(
                    u"Trying to add {0} to {1} regulars, but they were "
                    u"already one.".format(
                        regular, channel
                    )
                )
                message = u"{0}, {1} is already a regular?"
                self._message(channel, message.format(nick, regular))
                return

            self._add_regular(channel, regular)
            message = u"{0}, Added new regular: {1}"
            self._message(channel, message.format(nick, regular))
        elif action == u'del':
            if not self._is_regular(channel, regular):
                self.logger.info(
                    u"Trying to remove {0} from {1} regulars, but they "
                    u"weren't "
                    u"a regular there.".format(
                        regular, channel
                    )
                )
                message = u"{0}, {1} is not a regular?"
                self._message(channel, message.format(nick, regular))
                return

            self._remove_regular(channel, regular)
            message = u"{0}, Removed regular: {1}"
            self._message(channel, message.format(nick, regular))

    def _show_quote(self, channel, nick, args):
        """
        Handler for the "quote" -command, shows a quote on the channel

        :param channel: The channel the command was triggered on
        :param nick: The nick that triggered it
        :param args: The words on the line after the command
        :return: None
        """

        model = self._get_model(channel, u"quotes")
        quote_id, quote = model.get_random_quote()
        if quote:
            message = u"Quote #{0}: {1}".format(quote_id, quote)
            self._message(channel, message)

            self.logger.info(u"Showed quote for channel {0}: {1}".format(
                channel, quote
            ))
        else:
            message = u"No quotes in the database. Maybe you should add one?"
            self._message(channel, message)

            self.logger.info(u"No quotes for channel {0}".format(channel))

    def _add_quote(self, channel, nick, args, timestamp=None):
        """
        Handler for the "addquote" -command, adds a quote to the database

        :param channel: The channel the command was triggered on
        :param nick: The nick that triggered it
        :param args: The words on the line after the command
        :return: None
        """

        quote_text = " ".join(args)
        if len(quote_text) == 0:
            self.logger.info(u"Got 0 length addquote call from {0} in "
                             u"{1}?".format(nick, channel))

            message = u"{0}, ehh .. you gave me no quote?"
            self._message(channel, message.format(nick))
            return

        if not timestamp:
            timestamp = datetime.now()

        model = self._get_model(channel, "quotes")
        quote = model.create(
            quote=quote_text,
            year=int(timestamp.strftime("%Y")),
            month=int(timestamp.strftime("%m")),
            day=int(timestamp.strftime("%d"))
        )

        message = u"{0}, New quote added."
        self._message(channel, message.format(nick))

        self.logger.info(u"Added quote for {0}: {1}".format(channel, quote))

    def _del_quote(self, channel, nick, args):
        """
        Handler for the "delquote" command, removes a quote from the database

        :param channel: The channel the command was triggered on
        :param nick: The nick that triggered it
        :param args: The words on the line after the command
        :return: None
        """

        if len(args) == 0:
            self.logger.info(u"Got 0 length delquote call from {0} in "
                             u"{1}?".format(nick, channel))

            message = u"{0}, ehh .. you gave me no quote ID?"
            self._message(channel, message.format(nick))
            return

        quote_id = args[0]

        model = self._get_model(channel, "quotes")
        quote = model.filter(id=quote_id).first()

        if quote:
            quote.delete_instance()
            message = u"{0}, Quote removed.".format(nick)
            self.logger.info(
                u"Removed quote {0} for {1}".format(quote_id, channel)
            )
        else:
            message = u"{0}, no quote found with ID {1}".format(nick, quote_id)

        self._message(channel, message)

    #
    # Internal helper methods
    #

    def _set_command(self, channel, command, flags, user_level, code):
        """
        Save a command on the channel's database

        :param channel: Which channel
        :param command: What command
        :param flags: Command flags
        :param user_level: Minimum user level to access this command
        :param code: The Lua code for the command
        :return: None
        """

        model = self._get_model(channel, "commands")
        cmd = model.filter(command=command).first()

        if not cmd:
            cmd = model()
            cmd.command = command

        cmd.flags = json.dumps(flags)
        cmd.user_level = user_level
        cmd.code = code

        cmd.save()

        self.logger.info(u"Updated command {0} with user level {1}".format(
            command, user_level
        ))

    def _add_regular(self, channel, nick):
        """
        Add a regular to the channel

        :param channel: Which channel
        :param nick: The nick of the new regular
        :return: None
        """

        model = self._get_model(channel, "regulars")
        model.create(
            nick=nick
        )

        self.logger.info(u"Added regular {0} to {1}".format(nick, channel))

    def _remove_regular(self, channel, nick):
        """
        Remove a regular from the channel

        :param channel: Which channel
        :param nick: The nick of the old regular
        :return: None
        """

        model = self._get_model(channel, "regulars")
        regular = model.filter(nick=nick).first()

        if regular:
            regular.delete_instance()
            self.logger.info(u"Removed regular {0} from {1}".format(
                nick, channel
            ))

    def _add_to_blacklist(self, channel, nick, args):
        """
        Add an item to the blacklist
        :param channel:
        :param nick:
        :param args:
        :return:
        """

        parser = ArgumentParser()
        parser.add_argument("-b", "--banTime", default="10m")
        parser.add_argument("match", nargs='*')

        options = parser.parse_args(args)

        model = self._get_model(channel, "blacklist")

        rule = model()
        rule.match = " ".join(options.match)
        rule.banTime = options.banTime
        rule.save()

        self.blacklist_managers[channel].add_blacklist(rule)

        message = u"{nick}, added blacklist rule {match} with ID {id}".format(
            nick=nick, match=rule.match, id=rule.id
        )

        return message

    def _add_to_whitelist(self, channel, nick, args):
        """
        Add an item to the whitelist
        :param channel:
        :param nick:
        :param args:
        :return:
        """
        model = self._get_model(channel, "whitelist")

        rule = model()
        rule.match = " ".join(args)
        rule.save()

        self.blacklist_managers[channel].add_whitelist(rule)

        message = u"{nick}, added whitelist rule {match} with ID {id}".format(
            nick=nick, match=rule.match, id=rule.id
        )

        return message

    def _remove_from_blacklist(self, channel, nick, args):
        if len(args) == 0:
            self.logger.info(u"Got 0 length unblacklist call from {0} in "
                             u"{1}?".format(nick, channel))

            message = u"{0}, ehh .. you gave me no ID?"
            self._message(channel, message.format(nick))
            return

        row_id = args[0]

        model = self._get_model(channel, "blacklist")
        item = model.filter(id=row_id).first()

        if item:
            item.delete_instance()

            self.blacklist_managers[channel].remove_blacklist(row_id)

            message = u"{0}, blacklist item removed.".format(nick)
            self.logger.info(u"Removed blacklist item {0} for {1}".format(
                row_id, channel
            ))
        else:
            message = u"{0}, no blacklist item found with ID {1}".format(
                nick, row_id
            )

        return message

    def _remove_from_whitelist(self, channel, nick, args):
        if len(args) == 0:
            self.logger.info(u"Got 0 length unwhitelist call from {0} in "
                             u"{1}?".format(nick, channel))

            message = u"{0}, ehh .. you gave me no ID?"
            self._message(channel, message.format(nick))
            return

        row_id = args[0]

        model = self._get_model(channel, "whitelist")
        item = model.filter(id=row_id).first()

        if item:
            item.delete_instance()

            self.blacklist_managers[channel].remove_whitelist(row_id)

            message = u"{0}, whitelist item removed.".format(nick)
            self.logger.info(u"Removed whitelist item {0} for {1}".format(
                row_id, channel
            ))
        else:
            message = u"{0}, no whitelist item found with ID {1}".format(
                nick, row_id
            )

        return message

    def _update_channel_data(self, channel, key, value):
        """
        Save a single value to the channel's database

        :param channel: Which channel
        :param key: The name of the value
        :param value: The data to store
        :return: None
        """

        model = self._get_model(channel, "data")
        data = model.filter(key=key).first()

        if not data:
            data = model()
            data.key = key

        data.value = json.dumps(value)

        data.save()

    def _load_channel_data(self, channel):
        """
        Load all the channel's data values

        :param channel: Which channel
        :return: Python dict of all the stored values
        """

        model = self._get_model(channel, "data")
        entries = list(model.select())

        data = {}
        for entry in entries:
            data[entry.key] = json.loads(entry.value)

        return data

    def _initialize_command_managers(self):
        """
        Initialize all the command managers for all the channels, load our
        global Lua files in their Lua interpreters, and load the channel
        data and commands.

        :return: None
        """

        lua_files = self._find_lua_files()

        for channel in self.settings.CHANNEL_LIST:
            channel_data = self._load_channel_data(channel)
            cm = CommandManager(
                channel,
                self.wrapper,
                self.settings,
                channel_data,
                self.logger
            )

            for filename in lua_files:
                with open(filename, 'r') as handle:
                    code = handle.read()
                    self.logger.debug(u"Loading Lua for {0} from {1}".format(
                        channel, filename
                    ))
                    cm.load_lua(code)

            model = self._get_model(channel, "commands")
            commands = list(model.select())

            for command in commands:
                cm.load_command(
                    command.command,
                    json.loads(command.flags),
                    command.user_level,
                    command.code,
                    set=False
                )

            self.command_managers[channel] = cm

    def _initialize_blacklists(self):
        """
        Set up blacklist managers for all the channels
        :return:
        """

        for channel in self.settings.CHANNEL_LIST:
            manager = BlacklistManager(logger=self.logger)

            blacklist_model = self._get_model(channel, "blacklist")
            whitelist_model = self._get_model(channel, "whitelist")

            blacklist = list(blacklist_model.select())
            whitelist = list(whitelist_model.select())

            manager.set_data(blacklist, whitelist)

            self.blacklist_managers[channel] = manager

    def _find_lua_files(self):
        """
        Locate all Lua files we want to be globally included in our Lua runtime

        :return: Python list of the paths to the Lua files to be included
        """

        return glob(self.settings.LUA_INCLUDE_GLOB)

    def _initialize_models(self):
        """
        Set up our database connection and load up the model classes

        :return: None
        """

        self.db = Database(self.settings)
        self.db.run_migrations()
        for channel in self.settings.CHANNEL_LIST:
            self.channel_models[channel] = self.db.get_models(channel)

    def _get_model(self, channel, table):
        """
        Get the model instance for the given channel table

        :param channel: Which channel
        :param table: The name of the table, "regulars", "data", "commands",
                      or "quotes"
        :return: A peewee model for the table
        """

        return self.channel_models[channel][table]
