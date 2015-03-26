#!/usr/bin/env python
"""
Tool to extract all the quotes from the database.

Relies on settings.py to have the correct settings for database, and channels.
"""

from bot.database import Database
from argparse import ArgumentParser
import settings


if __name__ == "__main__":
    ap = ArgumentParser(description=__doc__)
    ap.add_argument(
        "channel", help="The channel to extract quotes from"
    )
    options = ap.parse_args()

    db = Database(settings)
    models = db.get_models(options.channel)

    for row in models["quotes"].select():
        print(row.quote)

    for row in models["notes"].select():
        print(u"{0} {1} {2}".format(row.gamename, row.starttime, row.notetime))