"""
Database abstraction layer
"""

from peewee import SqliteDatabase, Model, CharField, IntegerField, \
    BooleanField, TextField
from peewee import fn


class Database(object):
    """
    Simple database layer that provides channel specific peewee models
    """

    def __init__(self, settings):
        self.settings = settings
        self.db = None

    def get_models(self, channel):
        """
        Get channel specific data models

        :param channel: Name of the channel
        :return: Dict with models
        """

        channel = self._clean_channel(channel)
        db = self._get_db()

        class Regulars(Model):
            nick = CharField(unique=True)

            class Meta:
                database = db
                db_table = "regulars_{channel}".format(channel=channel)

        class Commands(Model):
            command = CharField(unique=True)
            want_user = BooleanField()
            user_level = CharField()
            code = TextField()

            class Meta:
                database = db
                db_table = "commands_{channel}".format(channel=channel)

        class Data(Model):
            key = CharField(unique=True)
            value = TextField()

            class Meta:
                database = db
                db_table = "data_{channel}".format(channel=channel)

        class Quotes(Model):
            quote = TextField(unique=True)

            class Meta:
                database = db
                db_table = "quotes_{channel}".format(channel=channel)

            @staticmethod
            def get_random_quote():
                """
                Get a random quote from the DB

                :return: Quote ID and text, or None, None
                """

                quote = Quotes.select().order_by(fn.Random()).limit(1).first()

                if quote:
                    return quote.id, quote.quote
                else:
                    return None, None

        model_map = {
            "regulars": Regulars,
            "commands": Commands,
            "data": Data,
            "quotes": Quotes
        }

        for key in model_map:
            model = model_map[key]

            if not model.table_exists():
                model.create_table()

        return model_map

    def _get_db(self):
        """
        Get a database connection, initialize it if not done so yet

        :return: SqliteDatabase instance
        """

        if not self.db:
            self.db = SqliteDatabase(self.settings.DATABASE_PATH)
            self.db.connect()

        return self.db

    def _clean_channel(self, channel):
        """
        Clean a channel name for use in table names

        :param channel: The channel name
        :return: A safe name
        """

        return channel.replace("#", "_")
