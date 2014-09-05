from threading import Timer


class Delayed(object):
    """
    Does a delayed Lua function call
    """

    def __init__(self, seconds, lua_function, lua, start=True):
        """
        :param seconds: Number of seconds to wait
        :param lua_function: The Lua function to execute
        :param lua: The Lua runtime to execute in
        :param start: Autostart the timer?
        :return:
        """

        self.seconds = seconds
        self.lua_function = lua_function
        self.lua = lua
        self.timer = None

        if start:
            self.start()

    def start(self):
        """
        Start the timer

        :return:
        """

        self.timer = Timer(self.seconds, self._timer_callback)
        self.timer.start()

    def cancel(self):
        """
        Stop/cancel the timer

        :return:
        """
        self.timer.cancel()

    def _timer_callback(self):
        """
        Called when the time has elapsed, calls the Lua function

        :return:
        """

        call_lua = self.lua.eval("""
        function (func)
            func()
        end
        """)

        call_lua(self.lua_function)


class Interval(Delayed):
    """
    Periodically call a Lua function
    """

    def _timer_callback(self):
        """
        Called when the time has elapsed, calls the Lua function,
        reschedules timer

        :return:
        """
        super(Interval, self)._timer_callback()
        self.start()
