import re
from bot.database import Migration


class FunctionPrefixMigration(Migration):
    def up(self, database, settings):
        for channel in settings.CHANNEL_LIST:
            db = database._get_db()
            models = database.get_models(channel)

            functions = models["commands"].select()

            for func in functions:
                code = re.sub(
                    r'function ([^(]+)\(',
                    r'function __chat__\1(',
                    func.code
                )
                func.code = code
                func.save()
