from typing import List
from contextlib import contextmanager
from contextlib import ExitStack
import functools
import logfire

class LogFireLogger:
    LOGFIRE_CONTEXTS = []

    @classmethod
    @contextmanager
    def logfire_context(cls, value: str):
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
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with LogFireLogger.logfire_context(context_name):
                    return func(*args, **kwargs)

            return wrapper

        return decorator

    @staticmethod
    def logfire_class_decorator(cls):
        for name, method in cls.__dict__.items():
            if callable(method):
                setattr(cls, name, LogFireLogger.logfire_method_decorator(f"{cls.__name__}.{name}")(method))
        return cls