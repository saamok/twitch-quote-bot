from irc.bot import SingleServerIRCBot


class IRCWrapper(SingleServerIRCBot):
    """Convenient wrapper for the irc class methods, rate limits the
    messages sent to the server to avoid being banned for spamming."""

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
