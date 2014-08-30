from Queue import Queue
from threading import Thread
from irc.bot import SingleServerIRCBot
from time import sleep


class Task(object):
    def __init__(self, method, *args, **kwargs):
        self.method = method
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return "<Task for method {0} with {1} args and {2} kwargs>".format(
            self.method,
            len(self.args),
            len(self.kwargs)
        )


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
        self.queue = Queue()
        self.thread = None

        if bot:
            self.queue_delay = bot.settings.QUEUE_DELAY
        else:
            self.queue_delay = 1

        serverList = []

        if password:
            self.logger.info("Connecting to {0}:{1} using a password".format(
                server, port
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

    def start(self):
        """Start the IRC connection and thread"""

        self._start_thread()
        super(IRCWrapper, self).start()

    def stop(self):
        """Stop our threads etc."""

        self.queue.put(None)

    def message(self, channel, message):
        """Request to send a message to the channel"""

        self.queue.put(Task(
            "_send_message",
            channel,
            message
        ))

    def is_oper(self, channel, nick):
        """Check if the user is an operator/moderator in the channel"""

        return self.channels[channel].is_oper(nick)

    # "Private" methods

    def _start_thread(self):
        """Start a thread that will work on the tasks"""

        def worker():
            while True:
                task = self.queue.get()

                if task == None:
                    return

                self._process_task(task)
                sleep(self.queue_delay)

        self.thread = Thread(target=worker)
        self.thread.daemon = True
        self.thread.start()

    def _process_task(self, task):
        """Process a single Task object"""

        method = getattr(self, task.method)
        if not method:
            raise ValueError("No method {0} in IRC wrapper?".format(
                task.method
            ))

        method(*task.args, **task.kwargs)

    def _send_message(self, channel, message):
        """Actually send a message on a channel"""

        self.logger.info("Delivering message to {0}: {1}".format(
            channel, message
        ))
        self.connection.privmsg(channel, message)

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
