import json
from bot.database import Migration
from peewee import OperationalError


class FlagsMigration(Migration):
    def up(self, database, settings):
        for channel in settings.CHANNEL_LIST:
            db = database._get_db()
            models = database.get_models(channel)

            if not self._check(db, models):
                continue

            old_commands = self._load_commands(db, models)

            models["commands"].drop_table()
            models["commands"].create_table()

            with db.transaction():
                models["commands"].insert_many(old_commands).execute()

    def _check(self, db, models):
        try:
            table = models["commands"]._meta.db_table
            sql = """
            SELECT flags FROM {0} LIMIT 1
            """.format(table)

            db.execute_sql(sql)
        except OperationalError:
            return True

        return False

    def _load_commands(self, db, models):
        table = models["commands"]._meta.db_table

        sql = """
        SELECT * FROM {0}
        """.format(table)

        result = db.execute_sql(sql)

        commands = []
        for row in result:
            id, command, want_user, user_level, code = row
            commands.append({
                "command": command,
                "flags": json.dumps({"want_user": want_user}),
                "user_level": user_level,
                "code": code
            })

        return commands

