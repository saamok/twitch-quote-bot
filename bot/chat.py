class Chat(object):
    """
    API for Lua to interact with the stream chat
    """

    def __init__(self, bot, channel):
        self.bot = bot
        self.channel = channel

    def message(self, text):
        """
        Send a message to the stream chat

        :param text: The message text
        :return:
        """

        self.bot._message(self.channel, text)

    def get_users(self):
        """
        Get the users currently in chat

        :return:
        """

        return self.bot.get_irc().get_users(self.channel)