import logging
from unittest import TestCase

from bot.blacklist import BlacklistManager

class Model(object):
    def __init__(self, rule_id, match, ban_time="1h"):
        self.id = rule_id
        self.match = match
        self.banTime = ban_time


class BlacklistTest(TestCase):
    """Make sure the Bot class seems sane"""

    def test_is_blacklisted(self):
        blacklist = [
            Model(1, "http://example.com/abc/*"),
            Model(2, "http://example.com/2/"),
            Model(3, "http://youtube.com")
        ]

        whitelist = [
            Model(1, "http://example.com/abc/lietu"),
            Model(2, "http://youtube.com/watch?v=fu2bgwcv43o")
        ]

        manager = BlacklistManager(logger=logging.getLogger("foo"))
        manager.set_data(blacklist, whitelist)

        res, rid, t = manager.is_blacklisted("Visit "
                                             "http://example.com/abc/def !")
        assert res is True
        assert rid == 1

        res, rid, t = manager.is_blacklisted("Visit http://example.com/abc/ !")
        assert res is True
        assert rid == 1

        res, rid, t = manager.is_blacklisted("Visit http://example.com/2/ !")
        assert res is True
        assert rid == 2

        res, rid, t = manager.is_blacklisted("http://youtube.com")
        assert res is True
        assert rid == 3

        res, rid, t = manager.is_blacklisted("Visit "
                                             "http://example.com/lietu !")
        assert res is False

        res, rid, t = manager.is_blacklisted("http://example.com/abc/lietu")
        assert res is False

        res, rid, t = manager.is_blacklisted("http://google.com")
        assert res is False

        res, rid, t = manager.is_blacklisted("http://youtube.com/watch?v="
                                             "fu2bgwcv43o")
        assert res is False

