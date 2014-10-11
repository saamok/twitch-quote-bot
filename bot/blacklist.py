import re


class BlacklistManager(object):
    """
    Manager for blacklist and whitelist functionalities
    """

    rule_regexp = "({rule})"
    rule_until_whitespace_regexp = "({rule}[^\s]*)"

    def __init__(self, logger=None):
        self.logger = logger
        self.blacklist = []
        self.whitelist = []


    def set_data(self, blacklist=None, whitelist=None):
        """
        Update the blacklist and whitelist data
        :param blacklist: List of blacklist rules
        :param whitelist: List of whitelist rules
        :return:
        """

        if blacklist is not None:
            self.blacklist = self._compile_rules(blacklist, True)

        if whitelist is not None:
            self.whitelist = self._compile_rules(whitelist)

    def add_blacklist(self, rule):
        """
        Add a new rule to blacklist
        :param rule:
        :return:
        """
        self.blacklist = self.blacklist + self._compile_rules([rule], True)

    def add_whitelist(self, rule):
        """
        Add a new rule to whitelist
        :param rule:
        :return:
        """
        self.whitelist = self.whitelist + self._compile_rules([rule])

    def remove_blacklist(self, rule_id):
        """
        Remove a rule from the blacklist
        :param rule_id:
        :return:
        """
        self.blacklist = [
            item
            for item in self.blacklist
            if item.id != rule_id
        ]

    def remove_whitelist(self, rule_id):
        """
        Remove a rule from the whitelist
        :param rule_id:
        :return:
        """
        self.whitelist = [
            item
            for item in self.whitelist
            if item.id != rule_id
        ]

    def is_blacklisted(self, line):
        """
        Check if anything on this line is blacklisted
        :param line:
        :return:
        """

        blacklist_hits = self._get_blacklist_hits(line)

        matched = False
        matched_rule = None
        matched_ban_time = None

        for match, rule_id, ban_time in blacklist_hits:
            self._log("Rule #{id} matched {match}".format(
                id=rule_id,
                match=match
            ))
            whitelist_id = self._is_on_whitelist(match)
            if not whitelist_id:
                if not matched_ban_time or ban_time > matched_ban_time:
                    matched = True
                    matched_rule = rule_id
                    matched_ban_time = ban_time
            else:
                self._log("However whitelist rule #{id} also matches".format(
                    id=whitelist_id
                ))

        return matched, matched_rule, matched_ban_time

    def _compile_rules(self, rules, until_whitespace=False):
        """
        Compile black- or whitelist rules to regular expressions
        :param rules:
        :return:
        """

        for rule_object in rules:
            if until_whitespace:
                base = self.rule_until_whitespace_regexp
            else:
                base = self.rule_regexp

            regex = base.format(rule=self._escape(
                rule_object.match
            ))

            rule_object.regex = re.compile(regex)

        return rules

    def _escape(self, rule):
        """
        Convert the given rule to one that can be injected into a regex
        :param rule:
        :return:
        """

        result = re.escape(rule)
        result = result.replace("\\*", "[^\s]*")
        return result

    def _get_blacklist_hits(self, line):
        """
        Get any and all occurrences of strings matching the blacklist in the
        text given
        :param line:
        :return:
        """

        result = []

        for rule in self.blacklist:
            match = rule.regex.search(line)

            if match:
                text = match.group(1)
                result.append(
                    (text, rule.id, self._parse_ban_time(rule.banTime))
                )
                line = line.replace(text, "")

        return result

    def _is_on_whitelist(self, string):
        """
        Check if the given matched string is on the whitelist
        :param string:
        :return:
        """

        for rule in self.whitelist:
            match = rule.regex.search(string)

            if match:
                return rule.id

        return False

    def _parse_ban_time(self, text):
        """
        Convert human readable timespan text to number of seconds

        >>> import bot.blacklist
        >>> m = bot.blacklist.BlacklistManager()
        >>> m._parse_ban_time("44s")
        44
        >>> m._parse_ban_time("1m")
        60
        >>> m._parse_ban_time("1h")
        3600
        >>> m._parse_ban_time("1d")
        86400
        >>> m._parse_ban_time("1w")
        604800
        >>> m._parse_ban_time("2w2d2h2m2s")
        1389722

        :param text:
        :return:
        """

        second_values = {
            "s": 1,
            "m": 60,
            "h": 3600,
            "d": 86400,
            "w": 604800
        }

        result = 0

        regex = "[0-9]+[smhdw]+"
        tokens = re.findall(regex, text)

        for token in tokens:
            key = token[-1:]
            multiplier = int(token[:-1])

            if key in second_values:
                seconds = second_values[key]
                result += seconds * multiplier

        return result

    def _log(self, message):
        """
        Relay any log messages to a logger, if we have one
        :param message:
        :return:
        """
        if self.logger:
            self.logger.debug("BLACKLIST: " + message)
