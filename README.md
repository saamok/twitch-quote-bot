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


Getting an OAuth token for Twitch chat IRC access
=================================================

You should visit these pages for help:

 * http://help.twitch.tv/customer/portal/articles/1302780-twitch-irc
 * http://twitchapps.com/tmi/
