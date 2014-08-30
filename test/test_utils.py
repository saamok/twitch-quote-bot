import bot.utils
from unittest import TestCase

class UtilsTest(TestCase):

    def test_human_readable_time(self):
        seconds = 181
        expected = "3 minute(s) 1 second(s)"

        output = bot.utils.human_readable_time(seconds)
        print(output)
        assert output == expected

        seconds = (60 * 60 * 24 * 365 * 70) + 3661
        expected = "70 year(s) 1 hour(s) 1 minute(s) 1 second(s)"

        output = bot.utils.human_readable_time(seconds)
        assert output == expected
