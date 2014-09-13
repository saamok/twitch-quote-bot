try:
    from urllib import urlencode
    from urllib2 import Request, urlopen
except ImportError:
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen


USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 " \
             "(KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36"


class TupleData(object):
    """
    Container where it's easy to push tuple values from Lua to for use in HTTP
    headers and data.

    >>> import bot.http
    >>> d = bot.http.TupleData()
    >>> d.add("options[]", "value1")
    >>> d.add("options[]", "value2")
    >>> str(d)
    'options%5B%5D=value1&options%5B%5D=value2'
    >>>

    """

    def __init__(self):
        self.data = []

    def add(self, key, value):
        """
        Add a key, value -combo to the tuple list

        :param key: The key on the tuple
        :param value: The value on the tuple
        """

        self.data.append((key, value))

    def __str__(self):
        """
        Convert the stored data into a URL encoded data string

        :returns: The data stored in this object
        """

        return urlencode(self.data)

    def items(self):
        """
        Provides compatibility with Python lists

        :returns: The tuples saved in this object
        """

        return self.data


class Http(object):
    """
    Simple HTTP layer for use with the Lua API

    Sends fake User-Agent string for a real browser instead of the default crap
    """

    def post(self, url, data=None, headers=None):
        """
        Do a POST request and return the response text

        :param url: Destination URL
        :param data: List of POST data via a TupleData object
        :param headers: List of request headers via a TupleData object
        :return: Request response body
        """
        request = Request(url, str(data), headers)
        request.add_header("User-Agent", USER_AGENT)
        response = urlopen(request)
        return response.read().decode('utf-8')

    def get(self, url, data=None, headers=None):
        """
        Do a GET request and return the response text

        :param url: Destination URL
        :param data: List of POST data via a TupleData object
        :param headers: List of request headers via a TupleData object
        :return: Request response body
        """
        if data:
            url += "?" + str(data)

        request = Request(url, headers=headers)
        response = urlopen(request)
        return response.read().decode('utf-8')
