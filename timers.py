"""Precision timer routines using 'perf_counter'."""
import time

class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class."""


class EcTimer:
    """Precision counters based on time.perf_counter.

    Each created instance uses independent timer
    """

    def __init__(self):
        self._start_time = None

    # classic back counting timer
    def set(self, timePeriod):
        """
        set and start timer.

        :param timePeriod: value in seconds as float
        :return: ---
        """

        self._start_time = timePeriod + time.perf_counter()

    def read(self):
        """
        Read remaning time. Zero if time elapsed

            :return:  remaining time
        """
        if self._start_time is not None:
            remain = self._start_time - time.perf_counter()
            if remain < 0:
                remain = 0
        else:
            remain = 0
        return remain

    # more functions for time measurement
    def elapsed(self):
        """
        Get time since start in seconds.

        :return: elapsed seconds as float
        """
        if self._start_time is not None:
            elapsed_time = time.perf_counter() - self._start_time
            print(f"Elapsed time: {elapsed_time:0.4f} seconds")
            return elapsed_time

    def stop(self):
        """Stop the timer and return the elapsed time

        :return: elapsed seconds as float
        """

        if self._start_time is None:
            raise TimerError(f"Timer is not running")

        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None
        print(f"Elapsed time: {elapsed_time:0.4f} seconds")
