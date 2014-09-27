#  Copy this file to settings.py and edit it

# The host and port of the server, if connecting to Twitch you probably
# don't need to change these
HOST = "irc.twitch.tv"
PORT = 6667
USE_SSL = False

# Details for logging in with the user you want to use for the bot
# More information on how to get the OAuth token in README.md
USER = "your_user_name"
OAUTH_TOKEN = "oauth:*************"

# Where do you want to store the database
DATABASE_PATH = "bot.sqlite"

# Configuration for channels and the the streamer names (for e.g. quotes)
# Usually if your twitch username is foobar you want to configure this as:
# { "#foobar": "FooBar" }
CHANNEL_LIST = {
    "#your_user_name": "Your User Name"
}

# If you want to log everything the bot does to a file, put the filename here
LOG_FILE = None

# What prefix do you want for all commands? E.g. with "!" you run !addquote,
# you could also set this to "foobar" and the command would be "foobaraddquote"
COMMAND_PREFIX = "!"

# Spin configuration, min and max spin results
SPIN_MIN = -100
SPIN_MAX = 250

# How many seconds do users need to wait between spins? 3600 = 1 hour
SPIN_TIMEOUT = 3600

# A glob pattern for including Lua code with, the code will be included
# globally, for most cases you probably want to use library pattern and
# store your files in the locations specified in LUA_PATH
LUA_INCLUDE_GLOB = "lua/*.lua"

# LUA_PATH environment variable, where Lua will look for files that are
# require()d
LUA_PATH = "lua/lib/?.lua;lua/lib/?/?.lua"

# These nicknames are always considered to have the highest user level (
# owner) by the bot
OWNER_USERS = [
    "lietu"
]

# Add a suffix when showing a quote, that displays the name of the streamer
# and time it was uttered on
QUOTE_AUTO_SUFFIX = True

# Python string format template for the suffix, supports the tags:
# {streamer} - Name of the streamer
# {year} - Current year
# {month} - Current month (2 digits)
# {day} - Current day of month (2 digits)
# For zero padding, use string formatting features, {day:02} will show zero
# padded 2 digit day always.
# E.g. for ISO 8601: {year}-{month:02}-{day:02} -> 2014-12-31 / 2015-01-01
QUOTE_AUTO_SUFFIX_TEMPLATE = " [{streamer} / {year}]"

# ----- ------- -----
# ----- Backups -----
# ----- ------- -----

# The path where you want to store the backups in
# A new folder will be created under this path for every backup, with the
# current time and date (YYYY-MM-DD_HHMMSS). The database backup will be
# stored inside the folder.
#
# Please make sure this folder is DEDICATED for the backups, as it WILL
# delete content from it when rotating the backups.
#
# You will likely want to change this.
BACKUP_BASEPATH = "/path/to/backups"

# The Unix permissions to set to the new backup directories
BACKUP_MODE = 0700

# How many backup copies to keep
BACKUP_COPIES = 336  # 2 weeks at 1 hour interval

# Command to use to compress the backup as a list suitable for
# subprocess.check_call. This means, you give the name of the command as the
# first item, and any arguments as separate items.
#
# Use the {filename} -tag to refer to the database file
# Set to None (not "None") if you want to disable compression for some reason
BACKUP_COMPRESS_CMD = ["gzip", "-9", "{filename}"]

# ----- --------- -----
# ----- Internals -----
# ----- --------- -----
#
# You probably don't need to touch these settings

# How many seconds the IRC layer will wait between processing outgoing
# commands, set this too low and Twitch can globally ban you or drop your
# messages, set it too high and the bot will seem seriously laggy.
QUEUE_DELAY = 2.5

