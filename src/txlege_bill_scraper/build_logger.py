from typing import List
from contextlib import contextmanager
from contextlib import ExitStack
import functools
import logfire


def scrubbing_callback(m: logfire.ScrubMatch):
    """
    Callback function to scrub sensitive data from log messages.

    Args:
        m (logfire.ScrubMatch): The match object containing the path and pattern match.

    Returns:
        str: The value of the match if the path and pattern match specific criteria.
    """
    if m.path == ("message", "e") and (
        m.pattern_match.group(0) == "session"
        or m.pattern_match.group(0) == "legislative_session"
    ):
        return m.value

    if m.path == ("attributes", "e") and (
        m.pattern_match.group(0) == "session"
        or m.pattern_match.group(0) == "legislative_session"
    ):
        return m.value


logfire.configure(scrubbing=False)
logfire.instrument_system_metrics(
    {
        "process.runtime.cpu.utilization": None,
        "system.cpu.simple_utilization": None,
        "system.memory.utilization": ["available"],
        "system.swap.utilization": ["used"],
    }
)

class LogFireLogger:
    """
    A class providing methods to manage logging contexts and decorators.
    """
    LOGFIRE_CONTEXTS = []

    @classmethod
    @contextmanager
    def logfire_context(cls, value: str):
        """
        Context manager to create and manage a logging context.

        Args:
            value (str): The name of the logging context.

        Yields:
            logfire.span: The topmost logging span.
        """
        cls.LOGFIRE_CONTEXTS.append(value)
        with ExitStack() as stack:
            # Build a list of all spans (reversed so the newest is last in the list)
            spans: List[logfire.span] = []
            for context_name in cls.LOGFIRE_CONTEXTS:
                span = logfire.span(context_name)
                stack.enter_context(span)
                spans.append(span)
            # The last one entered is the topmost (the current context)
            yield spans[0]
        cls.LOGFIRE_CONTEXTS.pop()

    @staticmethod
    def logfire_method_decorator(context_name):
        """
        Decorator to wrap a method with a logging context.

        Args:
            context_name (str): The name of the logging context.

        Returns:
            function: A decorator function.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with LogFireLogger.logfire_context(context_name):
                    return func(*args, **kwargs)
            return wrapper
        return decorator

    @staticmethod
    def logfire_class_decorator(cls):
        """
        Decorator to wrap all methods of a class with logging contexts.

        Args:
            cls (type): The class to decorate.

        Returns:
            type: The decorated class.
        """
        for name, method in cls.__dict__.items():
            if callable(method):
                setattr(cls, name, LogFireLogger.logfire_method_decorator(f"{cls.__name__}.{name}")(method))
        return cls