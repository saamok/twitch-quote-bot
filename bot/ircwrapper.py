"""
Handle the IRC connection for the bot
"""

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

from threading import Thread
from irc.bot import SingleServerIRCBot
from time import sleep


class Task(object):
    """
    Container for a IRCWrapper task that can be passed through the Queue
    between threads
    """

    def __init__(self, method, *args, **kwargs):
        self.method = method
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return "<Task:(method={0},{1} args,{2} kwargs>".format(
            self.method,
            len(self.args),
            len(self.kwargs)
        )


class IRCWrapper(SingleServerIRCBot):
    """
    Convenient wrapper for the irc class methods, rate limits the messages
    sent to the server to avoid being banned for spamming.
    """

    def __init__(self, logger=None, bot=None, channelList=None, nickname=None,
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

        if server:
            if password:
                self.logger.info(
                    "Connecting to {0}:{1} using a password".format(
                        server, port
                    ))
                serverList.append((server, port, password))
            else:
                self.logger.info(
                    "Connecting to {0}:{1} with no password".format(
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
        """
        Start the IRC connection and thread

        :return: None
        """

        self._start_thread()
        super(IRCWrapper, self).start()

    def stop(self):
        """
        Stop our threads etc.

        :return: None
        """

        self.queue.put(None)

    def message(self, channel, message):
        """
        Request to send a message to the channel, request is placed in output
        buffering task queue.

        :param channel: The channel to send the message to
        :param message: The message to be sent
        :return: None
        """

        self.queue.put(Task(
            "_send_message",
            channel,
            message
        ))

    def is_oper(self, channel, nick):
        """
        Check if the user is an operator/moderator in the channel

        :param channel: Which channel
        :param nick: What is the user's nick
        :return:
        """

        return self.channels[channel].is_oper(nick)

    def _start_thread(self):
        """
        Start a thread that will work on the tasks while preventing us from
        getting banned on Twitch servers etc.

        :return: None
        """

        def worker():
            """
            The thread's main function, will loop until a None -object is
            pushed to the task queue.

            :return: None
            """

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
        """
        Process a single Task

        :param task: An instance of the Task class
        :return: None
        """

        method = getattr(self, task.method)
        if not method:
            raise ValueError("No method {0} in IRC wrapper?".format(
                task.method
            ))

        method(*task.args, **task.kwargs)

    def _send_message(self, channel, message):
        """
        Actually send a message on a channel

        :param channel: The channel to send the message to
        :param message: The message to be sent
        :return: None
        """

        self.connection.privmsg(channel, message)

    def on_disconnect(self, connection, event):
        """
        Event handler run when the bot is disconnected from the server

        :param connection: The irc connection object
        :param event: An event containing more relevant info
        :return: None
        """

        self.logger.warn("Got disconnected from server: {0}".format(
            repr(event)
        ))

    def on_welcome(self, connection, event):
        """
        Event handler run after connection to server has been established,
        joins the channels the bot should be on.

        :param connection: The irc connection object
        :param event: An event containing more relevant info
        :return: None
        """

        self.logger.info("Connected to server, joining channels...")

        for channel in self.channelList:
            self.logger.info("Joining channel {0}".format(channel))
            connection.join(channel)

    def on_join(self, connection, event):
        """
        Event handler run when the bot joins a channel, and in case of
        Twitch for some other unknown reason(s) as well.

        :param connection: The irc connection object
        :param event: An event containing more relevant info
        :return: None
        """

        channel = self._get_event_channel(event)
        self.logger.info("Joined {0}".format(channel))

    def on_pubmsg(self, connection, event):
        """
        Event handler run when the bot seems a new message on any channel

        :param connection: The irc connection object
        :param event: An event containing more relevant info
        :return: None
        """

        text = self._get_event_text(event)
        channel = self._get_event_channel(event)

        command, args = self._get_command(text)

        if command:
            nick = self._get_event_nick(event)

            self.bot.irc_command(channel, nick, command, args)

    def _get_event_channel(self, event):
        """
        Extract the channel name from the given event

        :param event: An event object
        :return: The channel name the event occured on
        """

        return event.target

    def _get_event_text(self, event):
        """
        Extract the message text from a message event

        :param event: A message event
        :return: The message text
        """

        return event.arguments[0]

    def _get_event_nick(self, event):
        """
        Get the nick for the user that triggered this message event

        :param event: A message event
        :return: The user's nick
        """

        return event.source.nick

    def _get_command(self, text):
        """
        Extract any command on the given chat line

        >>> from bot.ircwrapper import IRCWrapper
        >>> i = IRCWrapper()
        >>> i._get_command("!def")
        ('def', [])
        >>> i._get_command("!foo bar")
        ('foo', ['bar'])
        >>> i._get_command("abc 123")
        (None, 'abc 123')

        :param text: A line of text from the chat
        :return: Command name and remainder text, or if no command found
                 None, original text
        """

        if not text.startswith(self.commandPrefix):
            return None, text

        # Strip off the command prefix
        text = text[len(self.commandPrefix):].strip()

        # Take the first word, in lowercase
        parts = text.split(' ')
        command = parts[0].lower()
        args = parts[1:]

        return command, args
