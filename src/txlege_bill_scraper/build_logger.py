from contextlib import contextmanager
from contextlib import ExitStack
import logfire

class LogFireLogger:
    LOGFIRE_CONTEXTS = []

    @classmethod
    @contextmanager
    def logfire_context(cls, value: str):
        cls.LOGFIRE_CONTEXTS.append(value)
        with ExitStack() as stack:
            # Build a list of all spans (reversed so the newest is last in the list)
            spans = []
            for context_name in cls.LOGFIRE_CONTEXTS:
                span = logfire.span(context_name)
                stack.enter_context(span)
                spans.append(span)
            # The last one entered is the topmost (the current context)
            yield spans[0]
        cls.LOGFIRE_CONTEXTS.pop()