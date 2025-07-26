"""
mcmas.util.lme.
"""

import logging
import os

from rich.console import Console
from rich.default_styles import DEFAULT_STYLES
from rich.logging import RichHandler
from rich.style import Style
from rich.theme import Theme

THEME = Theme(
    {
        **DEFAULT_STYLES,
        **{
            "logging.keyword": Style(bold=True, color="yellow"),
            # "logging.level.notset": Style(dim=True),
            "logging.level.debug": Style(color="green"),
            "logging.level.info": Style(
                dim=True,
                # color="blue",
            ),
            "logging.level.warning": Style(color="yellow"),
            "logging.level.error": Style(color="red", dim=True, bold=True),
            "logging.level.critical": Style(
                color="red",
                bold=True,
                # reverse=True
            ),
            "log.level": Style.null(),
            "log.time": Style(color="cyan", dim=True),
            "log.message": Style.null(),
            "log.path": Style(dim=True),
        },
    }
)

CONSOLE = Console(
    theme=THEME,
    stderr=True,
    color_system="auto",
)

print = CONSOLE.print


class Fake:
    warning = debug = info = critical = lambda *args, **kwargs: None


def get_logger(
    name,
    fake=False,
):
    """
    Utility function for returning a logger with standard
    formatting patterns, etc.
    """
    if fake:
        return Fake()
    log_handler = RichHandler(
        rich_tracebacks=True,
        console=CONSOLE,
        show_time=False,
    )

    logging.basicConfig(
        format="%(message)s",
        datefmt="[%X]",
        handlers=[log_handler],
    )
    FormatterClass = logging.Formatter
    formatter = FormatterClass(
        fmt=" ".join(["%(name)s", "%(message)s"]),
        datefmt="",
    )
    log_handler.setFormatter(formatter)

    logger = logging.getLogger(name)

    MCMAS_LOG_LEVEL = os.environ.get("MCMAS_LOG_LEVEL", "info").upper()
    logger.setLevel(MCMAS_LOG_LEVEL)
    return logger
