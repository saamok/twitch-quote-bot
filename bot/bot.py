from glob import glob
import json
from lupa import LuaError
from .commandmanager import CommandManager, CommandPermissionError
from .database import Database


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
        self.channel_models = {}
        self.db = None

    def __del__(self):
        if self.ircWrapper:
            self.ircWrapper.stop()

    #
    # Public API
    #

    def run(self):
        """Run the bot until we want to stop"""

        self.logger.info("Starting bot...")

        self._initialize_models()

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

    #
    # Internal API
    #

    def _message(self, channel, message):
        """Send a message to a channel"""

        self.logger.debug("Sending message to {0}: {1}".format(
            channel, message
        ))

        self.ircWrapper.message(channel, message)

    def _is_core_command(self, command):
        """Check if the command we got is actually a command we support"""

        return command in [
            "addquote",
            "delquote",
            "quote",
            "reg",
            "def"
        ]

    def _get_user_level(self, channel, nick):
        """Figure out the user's level on the channel"""

        level = "user"

        if self._is_mod(channel, nick):
            level = "mod"
        elif self._is_regular(channel, nick):
            level = "reg"

        return level

    def _can_run_command(self, channel, nick, command):
        """Is this guy allowed to run the command in this channel?"""

        user_level = self._get_user_level(channel, nick)

        if user_level == "mod":
            # Mods can do whatever they want
            return True
        elif command in ("addquote", "quote") and user_level == "reg":
            return True

        return False

    def _is_mod(self, channel, nick):
        """Check if the given user is a mod on the given channel"""

        return self.ircWrapper.is_oper(channel, nick)

    def _is_regular(self, channel, nick):
        """Is this guy on the regulars list?"""

        model = self._get_model(channel, "regulars")
        return model.filter(nick=nick).exists()

    #
    # Chat commands
    #

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

        model = self._get_model(channel, "quotes")
        quote_id, quote = model.get_random_quote()
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

    def _add_quote(self, nick, channel, args):
        """Add a quote to the database"""

        quote_text = " ".join(args)
        if len(quote_text) == 0:
            self.logger.info("Got 0 length addquote call from {0} in "
                             "{1}?".format(nick, channel))

            message = "{0}, ehh .. you gave me no quote?"
            self._message(channel, message.format(nick))
            return

        model = self._get_model(channel, "quotes")
        quote = model.create(
            quote=quote_text
        )

        message = "{0}, New quote added."
        self._message(channel, message.format(nick))

        self.logger.info("Added quote for {0}: {1}".format(channel, quote))

    def _del_quote(self, nick, channel, args):
        """Remove a quote from the database"""

        if len(args) == 0:
            self.logger.info("Got 0 length delquote call from {0} in "
                             "{1}?".format(nick, channel))

            message = "{0}, ehh .. you gave me no quote ID?"
            self._message(channel, message.format(nick))
            return

        quote_id = args[0]

        model = self._get_model(channel, "quotes")
        quote = model.filter(id=quote_id).first()

        if quote:
            quote.delete_instance()
            message = "{0}, Quote removed.".format(nick)
            self.logger.info("Removed quote {0} for {1}".format(quote_id, channel))
        else:
            message = "{0}, no quote found with ID {1}".format(nick, quote_id)

        self._message(channel, message)

    #
    # Internal helper methods
    #

    def _set_command(self, channel, command, want_user, user_level, code):
        """Save a command on the channel"""

        model = self._get_model(channel, "commands")
        cmd = model.filter(command=command).first()

        if not cmd:
            cmd = model()
            cmd.command = command

        cmd.want_user = want_user
        cmd.user_level = user_level
        cmd.code = code

        cmd.save()

        self.logger.info("Updated command {0} with user level {1}".format(
            command, user_level
        ))

    def _add_regular(self, channel, nick):
        """Add a new regular to channel"""

        model = self._get_model(channel, "regulars")
        model.create(
            nick=nick
        )

        self.logger.info("Added regular {0} to {1}".format(nick, channel))

    def _remove_regular(self, channel, nick):
        """Remove a regular from the channel"""

        model = self._get_model(channel, "regulars")
        regular = model.filter(nick=nick).first()

        if regular:
            regular.delete_instance()
            self.logger.info("Removed regular {0} from {1}".format(
                nick, channel
            ))

    def _update_channel_data(self, channel, key, value):
        """Update a single value for this channel's data"""

        model = self._get_model(channel, "data")
        data = model.filter(key=key).first()

        if not data:
            data = model()
            data.key = key

        data.value = json.dumps(value)

        data.save()

    def _load_channel_data(self, channel):
        """Load stored channel data"""

        model = self._get_model(channel, "data")
        entries = list(model.select())

        data = {}
        for entry in entries:
            data[entry.key] = json.loads(entry.value)

        return data

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

            model = self._get_model(channel, "commands")
            commands = list(model.select())

            for command in commands:
                cm.load_command(
                    command.command,
                    command.want_user,
                    command.user_level,
                    command.code,
                    set=False
                )

            self.command_managers[channel] = cm

    def _find_lua_files(self):
        return glob(self.settings.LUA_INCLUDE_GLOB)

    def _initialize_models(self):
        """Set up our database connection and load up the model classes"""

        self.db = Database(self.settings)
        for channel in self.settings.CHANNEL_LIST:
            self.channel_models[channel] = self.db.get_models(channel)

    def _get_model(self, channel, table):
        return self.channel_models[channel][table]
