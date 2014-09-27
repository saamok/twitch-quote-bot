"""
Database abstraction layer
"""

import importlib
import inspect
import json
import os
from peewee import SqliteDatabase, Model, CharField, IntegerField, \
    BooleanField, TextField
from peewee import fn


class Migration(object):
    def up(self, database, settings):
        raise NotImplementedError("Migration up() not implemented")


class Database(object):
    """
    Simple database layer that provides channel specific peewee models
    """

    def __init__(self, settings):
        self.settings = settings
        self.db = None
        self.debug = False

    def run_migrations(self):
        """
        Run any migrations not previously executed

        :return:
        """

        db = self._get_db()

        class DBState(Model):
            migration = CharField(unique=True)

            class Meta:
                database = db

        if not DBState.table_exists():
            DBState.create_table()

        migration_modules = self._find_migrations()
        if self.debug:
            print("Migration modules: " + ", ".join(migration_modules))

        for module_name in migration_modules:
            module = importlib.import_module(module_name)

            if self.debug:
                print("Processing migration module " + module_name)

            for key in module.__dict__:
                if key == "Migration":
                    if self.debug:
                        print("Skipping " + key)
                    continue

                if DBState.filter(migration=key).exists():
                    if self.debug:
                        print("Migration " + key + " already run")
                    continue

                item = module.__dict__[key]

                if inspect.isclass(item) and issubclass(item, Migration):
                    if self.debug:
                        print("Running migration " + key)
                    instance = item()
                    instance.up(self, self.settings)

                    DBState.create(migration=key)
                else:
                    if self.debug:
                        print("Skipping " + key)

    def _find_migrations(self):
        """
        Find any and all database migrations

        :return:
        """
        migrations_path = os.path.realpath(os.path.join(
            os.path.join(os.path.dirname(__file__), ".."),
            "db_migrations"
        ))

        files = sorted(os.listdir(migrations_path))

        modules = [
            "db_migrations." + filename[:-3]
            for filename in files
            if filename[-3:] == ".py" and filename != "__init__.py"
        ]

        return modules

    def get_models(self, channel):
        """
        Get channel specific data models

        :param channel: Name of the channel
        :return: Dict with models
        """

        raw_channel = channel
        channel = self._clean_channel(channel)
        db = self._get_db()
        settings = self.settings


        class Regulars(Model):
            nick = CharField(unique=True)

            class Meta:
                database = db
                db_table = "regulars_{channel}".format(channel=channel)

        class Commands(Model):
            command = CharField(unique=True)
            flags = TextField()
            user_level = CharField()
            code = TextField()

            _flag_data = None

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
            year = IntegerField()
            month = IntegerField()
            day = IntegerField()

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
                    if settings.QUOTE_AUTO_SUFFIX:
                        quoteText = quote.quote + Quotes._get_quote_suffix(
                            quote
                        )
                    else:
                        quoteText = quote.quote

                    return quote.id, quoteText
                else:
                    return None, None

            @staticmethod
            def _get_quote_suffix(quote):
                return settings.QUOTE_AUTO_SUFFIX_TEMPLATE.format(
                    streamer=settings.CHANNEL_LIST[raw_channel],
                    year=quote.year,
                    month=quote.month,
                    day=quote.day
                )

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
