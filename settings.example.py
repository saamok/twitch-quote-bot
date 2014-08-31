# Copy this file to settings.py and edit it

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

# What channels to join? Usually if your twitch username is foobar you want
# to add #foobar
CHANNEL_LIST = [
    "#your_user_name"
]

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

# ----- --------- -----
# ----- Internals -----
# ----- --------- -----
#
# You probably don't need to touch these settings

# How many seconds the IRC layer will wait between processing outgoing
# commands, set this too low and Twitch can globally ban you or drop your
# messages, set it too high and the bot will seem seriously laggy.
QUEUE_DELAY = 2.5

