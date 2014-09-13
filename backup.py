#!/usr/bin/env python

import os
import sys
from shutil import copy, rmtree
from datetime import datetime
from subprocess import check_call
import settings


def _error(message):
    """
    Show an error message and exit

    :param message: The error message
    :raise SystemExit:
    """
    print(message)
    print("")
    print("Check your settings.py -file.")
    sys.exit(1)


def _check_settings():
    """
    Check that the BACKUP_ settings look valid

    :raise SystemExit: In case of errors
    :return: None
    """
    if not settings.BACKUP_BASEPATH:
        _error("No BACKUP_BASEPATH set")
    if not os.path.isdir(settings.BACKUP_BASEPATH):
        _error("BACKUP_BASEPATH does not exist, or is not a directory.")
    if not settings.BACKUP_MODE:
        _error("BACKUP_MODE is not set, try e.g. 0700")
    if not settings.BACKUP_COPIES:
        _error("BACKUP_COPIES is not configured")
    if settings.BACKUP_COMPRESS_CMD:
        if not "{filename}" in settings.BACKUP_COMPRESS_CMD:
            _error("BACKUP_COMPRESS_CMD does not have {filename} tag")


def _compress(filename):
    """
    Compress the given path, if settings are configured for compression

    :param filename: The path to the file to be compressed
    :return: None
    """

    if settings.BACKUP_COMPRESS_CMD:
        cmd = settings.BACKUP_COMPRESS_CMD

        for i, value in enumerate(cmd):
            if value == "{filename}":
                cmd[i] = filename

        check_call(cmd)


def _create_backup():
    """
    Create a new backup of the database

    :return: None
    """

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    location = os.path.join(settings.BACKUP_BASEPATH, timestamp)
    os.makedirs(location, settings.BACKUP_MODE)

    destination = os.path.join(
        location,
        os.path.basename(settings.DATABASE_PATH)
    )

    copy(settings.DATABASE_PATH, destination)
    _compress(destination)

    return location


def _delete_old_backups():
    """
    Make sure we only have the number of backups specified in config.
    Delete oldest backups first when deleting excess backups.

    :return:
    """

    backups = os.listdir(settings.BACKUP_BASEPATH)
    extra = len(backups) - settings.BACKUP_COPIES

    if extra >= 1:
        backups = [
            os.path.join(settings.BACKUP_BASEPATH, item)
            for item in backups
        ]

        backups.sort(key=lambda item: os.stat(item).st_mtime)

        extras = backups[0:extra]
        for backup in extras:
            print("Deleting obsolete backup {0}".format(backup))
            rmtree(backup)


if __name__ == "__main__":
    _check_settings()
    location = _create_backup()
    print("Created new backup at {0}".format(location))
    _delete_old_backups()
