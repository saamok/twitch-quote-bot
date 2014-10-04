import json
import operator
from bot.database import Migration


class CurrencyMigration(Migration):
    def up(self, database, settings):
        for channel in settings.CHANNEL_LIST:
            db = database._get_db()
            models = database.get_models(channel)

            if not self._check(db, models):
                continue

            xp_data = self._load_data(models, "xp_data")
            spin_data = self._load_data(models, "spin_data")

            currencies = {}
            last_spin_time = {}

            xp_currency = settings.XP_CURRENCY
            spin_currency = settings.SPIN_CURRENCY

            currencies[xp_currency] = {}
            currencies[spin_currency] = {}

            for key in xp_data:
                if key in settings.IGNORE_USERS:
                    continue
                value = xp_data[key]
                currencies[xp_currency][key] = value

            for key in spin_data:
                if key in settings.IGNORE_USERS:
                    continue
                data = spin_data[key]
                last_spin_time[key] = data["last_spin_time"]
                value = data["value"]
                if key in currencies[spin_currency]:
                    value = value + currencies[spin_currency][key]
                currencies[spin_currency][key] = value

            hs_data = sorted(
                currencies[spin_currency].items(),
                key=operator.itemgetter(1)
            )
            hs_data.reverse()
            hs_data = hs_data[:3]

            highscores = []
            for user, value in hs_data:
                highscores.append({"value": value, "user": user})

            self._set_data(models, spin_currency + "_highscores", highscores)
            self._set_data(models, spin_currency + "_last_spin", last_spin_time)
            for key in currencies:
                self._set_data(models, key, currencies[key])

            self._clean_old(db, models)

    def _check(self, db, models):
        table = models["data"]._meta.db_table
        sql = """
        SELECT * FROM {0} WHERE `key` IN("xp_data", "spin_data", "spin_highscores")
        """.format(table)

        row = db.execute_sql(sql).fetchone()
        if row is None:
            return False

        return True

    def _clean_old(self, db, models):
        table = models["data"]._meta.db_table
        sql = """
        DELETE FROM {0} WHERE `key` IN("xp_data", "spin_data", "spin_highscores")
        """.format(table)

        db.execute_sql(sql)

    def _load_data(self, models, key):
        data = models["data"].filter(key=key).first()

        if data is None:
            return {}

        return json.loads(json.loads(data.value))

    def _set_data(self, models, key, value):
        data = models["data"]()
        data.key = key
        data.value = json.dumps(json.dumps(value))

        data.save()
