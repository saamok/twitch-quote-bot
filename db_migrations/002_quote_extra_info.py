
from datetime import datetime
from bot.database import Migration
from peewee import OperationalError


class QuotesExtraInfoMigration(Migration):
    def up(self, database, settings):
        for channel in settings.CHANNEL_LIST:
            db = database._get_db()
            models = database.get_models(channel)

            if not self._check(db, models):
                continue

            old_quotes = self._load_quotes(db, models)

            models["quotes"].drop_table()
            models["quotes"].create_table()

            with db.transaction():
                models["quotes"].insert_many(old_quotes).execute()

    def _check(self, db, models):
        try:
            table = models["quotes"]._meta.db_table
            sql = """
            SELECT `year` FROM {0} LIMIT 1
            """.format(table)

            db.execute_sql(sql)
        except OperationalError:
            return True

        return False

    def _load_quotes(self, db, models):
        table = models["quotes"]._meta.db_table

        sql = """
        SELECT * FROM {0}
        """.format(table)

        result = db.execute_sql(sql)

        quotes = []
        now = datetime.now()
        for row in result:
            id, quote = row
            quotes.append({
                "quote": quote,
                "year": int(now.strftime("%Y")),
                "month": int(now.strftime("%m")),
                "day": int(now.strftime("%d"))
            })

        return quotes

