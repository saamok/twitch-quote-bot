twitch-quote-bot
================

A bot mainly for Twitch channels, but can be used for other purposes as well.
 
The bot supports writing custom commands using Lua, and saves it's states in
 an sqlite database.


Current build status
====================

[![Build Status](https://travis-ci.org/lietu/twitch-quote-bot.svg?branch=master)](https://travis-ci.org/lietu/twitch-quote-bot)


Requirements
============
* Python 2.6 - 3.3
* pip
* lua (5.1, 5.2 or luajit should work)

Optional:
* virtualenv
* virtualenvwrapper

How to install prerequisites in Ubuntu:
```
sudo apt-get install python-pip lua5.1 liblua5.1-dev
sudo pip install virtualenv virtualenvwrapper
```

And on RHEL/CentOS/Fedora/similar:
```
# Enable EPEL repos for python-pip, for CentOS 6
rpm -Uvh http://ftp.linux.ncsu.edu/pub/epel/6/i386/epel-release-6-8.noarch.rpm

yum -y install python-setuptools python-pip python-devel lua lua-devel gcc
pip install virtualenv virtualenvwrapper
```

Setup
=====

 1. Get the code from GitHub.
 1. (Optional) Create virtualenv
    ```
    source $(which virtualenvwrapper.sh)
    mkvirtualenv virtualenv
    # In the future, instead run: ```workon virtualenv```
    ```
 1. Install dependencies
    ```
    pip install -r requirements.txt
    # You might have to prepend sudo if not using virtualenv
    ```
 1. Copy settings.example.py to settings.py, and edit to needs
 1. Run the bot: ```python -m bot```
    For Python 2.6 you'll have to use ```python -m bot.__main__```


Getting an OAuth token for Twitch chat IRC access
=================================================

You should visit these pages for help:

 * http://help.twitch.tv/customer/portal/articles/1302780-twitch-irc
 * http://twitchapps.com/tmi/


What if I want to stop using the bot?
=====================================

Getting rid of the bot itself is fairly easy, just stop it on the server you
 are running it on (press CTLR+C a few times)
 
However, you probably want access to your valued data as well. The bot's 
database is implemented using a very widely known engine called SQLite. 
There are plenty of tools you can use to take the bot.sqlite (default name) 
database and extract whatever data you want from it.
 
Quotes will probably be the only data actually useful outside of this bot, 
so there is a separate tool just for extracting them, dump_quotes.py.

Usage is fairly simple, call it and give it your channel's name (e.g. #lietu):
```
python dump_quotes.py "#lietu"
```

Notice the quotes in the example above, they are important to make sure your
 shell does not think you are writing a comment.

If you want to extract the quotes to a file, just redirect the output:
```
python dump_quotes.py "#lietu" > quotes.txt
```


Backup tool
===========

Your data is important, which is why there's a bundled backup tool with the 
bot.

The tool handles:
 * Keeping a given number of backups (e.g. 30)
 * Optionally compressing the backups (with gzip)
 
The settings for the backups are also in settings.py and should be fairly 
easy to understand.

To schedule the backups you need to use your crontab or other scheduling 
system. E.g. on linux, run:
```
crontab -e
```

Check the path to your python executable (usually /usr/bin/python):
```
which python
```

And add the following line (replace */path/to/* and */usr/bin/python* with the 
correct paths):
```
0 * * * *   /usr/bin/python /path/to/backup.py > /dev/null
```

 
Custom commands
===============

You can add custom commands to the bot via the chat interface if you are a 
moderator.

The command for defining lua functions is "def" (add your prefix, e.g. !).

The syntax is:
```
!def [--want_user] [--quoted] [--user_level=userlevel] [--args=arguments] 
command_name <lua code>
```

The --want_user -option makes the defined function receive the calling 
user's name as the an argument called "user" (the first argument).

The --quoted -option changes how arguments are processed, so it is possible to
give arguments with multiple words in them, for e.g. Strawpoll creation. 
This works so that "quoted strings" count only for a single argument. Both 
single- (') and double quotes (") work.

The short versions of argument names are:
 * --user_level = -ul
 * --args = -a
 * --want_user = -w
 * --quoted = -q

Any value returned by the function will be output back in chat by the bot.

So assuming your using the default prefix of "!", you can e.g. create a 
function that greets people on the channel:
```
!def -ul=mod -a=user hello return "Hi, " .. user
```

And you'd call that function e.g. ```!hello lietu```.

The def command allows limiting user access via the -ul= or --user_level= 
argument, valid values are: "user", "reg", "mod", and "owner" (not yet 
implemented)

You can define what arguments your function accepts from the chat using -a= or
 --args=, "..." is a lua magic argument that gives all the given arguments 
 in a variable called "arg", and it works fine with this bot.
  
```
!def -ul=reg --args=... sum 
!def --args=user,gift gift return user .. ", please accept this " .. gift
```

The functions will automatically be persisted to the sqlite database.


Lua code files
==============

You can add custom Lua code to the bot by writing them in .lua files in the 
lua/ -folder (or whatever you configured LUA_INCLUDE_GLOB for). There will 
not be a interface for the chat created automatically for these commands, 
but it's fairly easy for you to add the interface to a complex Lua 
application separately.

By default, there is a simple example in lua/example.lua, 
and you can add a chat interface to it quite simply:
```
!def --args=... sum return sum_example(unpack(arg))
```

And then just call it via the newly created custom command:
```
!sum 1 2 3
```

Lua library files
=================

In addition to loading global code, if you're interested in doing things 
"the right way", you can also add your Lua modules as libraries by placing 
your code under ```lib/library.lua```, or ```lib/library/library.lua```. 

This makes it possible for the functions (or other libraries) that need your 
code to run ```require("library")``` to access the code via your public 
methods.
 
Check for examples on this in the ```lua/lib/``` -directory. 

There are some pre-existing features that can be integrated easily from the 
Lua libraries to chat functions.

*Wheel of fortune*
```
!def --want_user --user_level=user spin local spin = require("spin"); return
 spin.spin(user)
!def --user_level=user highscores local spin = require("spin"); return
 spin.highscores()
```

Usage in chat after that is quite simple:
```
!spin
!highscores
```

*Strawpoll*

Create new Strawpolls via the bot.

```
!def --quoted --user_level=mod --args=title,... poll local sp = 
 require("strawpoll"); sp.create(title, unpack(arg))
```

Usage in chat after that:
```
!poll "My new poll" "Option 1" "Option 2" ...
```

The bot will show the URL to the new Strawpoll in the chat.


*XP*

Viewers in the chat will gain XP over time, and will be able to check their 
current XP on demand.

```
!def --user_level=user --want_user xp local xp = require("xp"); return user 
.. ", you currently have " .. xp.get_user_xp(user) .. " XP!"
```

And usage in chat:
```
!xp
```


Development environment
=======================

The development environment is built into the project via Vagrant.

To start using the development environment, install the following:

 * [Vagrant](https://www.vagrantup.com/)
 * [VirtualBox](https://www.virtualbox.org/)

After these are installed, you can boot up the Vagrant virtual machine.

Open a terminal, and change to the root directory of the project, 
then tell Vagrant to boot up the machine:

```
vagrant up
```

Once the VM is up, you can connect to it over SSH.

You can open your favorite SSH client (e.g. [KiTTY](http://www.9bis
.net/kitty/) on Windows) by using the IP address ```172.30.30.30```.

Alternatively on Linux and Mac OS X you can connect to it with:
```
vagrant ssh
```

User and password are both: ```vagrant```

To get to the development environment, you need to switch users:
```
sudo su - bot
```

Then activate the bot virtual environment:
```
workon bot
```

The source code is located on the virtual machine in /src, 
you might want to go there:
```
cd /src
```

Running tests
=============

When you have your Vagrant based development environment (or any other 
correctly set up environment) running, and you're in the root of the source 
folder you can run the unit tests via nose:
```
nosetests
```

If using the Vagrant VM in Windows, the shared folder causes some minor 
issues, you can work around that by telling nose to also include executable 
files in it's search for valid tests:
```
nosetests --exe
```

Code documentation
==================

You can generate HTML code documentation from the source code with Sphinx by
going to the docs/ folder and telling Sphinx to rebuild the HTML and run the
doctest tests embedded in the source at the same time:
```
make html doctests
```

On the Vagrant VM be sure to have activated the development virtualenv and 
run the command in ```/src/docs```


Salt Stack
==========

The development environment VM configuration is managed with Salt Stack.

If you make changes within the salt/ -directory, you can tell vagrant to 
apply the changes via Salt:
```
vagrant provision
```

Also if you pull changes from GitHub, you should probably run that command 
before trying to continue using the VM.

