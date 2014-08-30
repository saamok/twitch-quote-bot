twitch-quote-bot
================

A simple bot, mainly for Twitch channels, but can be used for other purposes
 as well.


Current build status
====================

[![Build Status](https://travis-ci.org/lietu/twitch-quote-bot.svg?branch=master)](https://travis-ci.org/lietu/twitch-quote-bot)


Requirements
============
* Python 2.6 - 3.3
* pip

Optional:
* virtualenv
* virtualenvwrapper

How to install prerequisites in ubuntu:
    sudo apt-get install python-pip
    sudo pip install virtualenv
    sudo pip install virtualenvwrapper


Setup
=====

 1. Get the code from GitHub.
 1. (Optional) Create virtualenv
    source $(which virtualenvwrapper.sh)
    mkvirtualenv virtualenv
    # In the future, instead run: ```workon virtualenv```
 1. Install dependencies
    pip install -r requirements.txt
    # You might have to prepend sudo if not using virtualenv
 1. Copy settings.example.py to settings.py, and edit to needs
 1. Run the bot: ```python -m bot```
    For Python 2.6 you'll have to use ```python -m bot.__main__```


Getting an OAuth token for Twitch chat IRC access
=================================================

You should visit these pages for help:

 * http://help.twitch.tv/customer/portal/articles/1302780-twitch-irc
 * http://twitchapps.com/tmi/


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
