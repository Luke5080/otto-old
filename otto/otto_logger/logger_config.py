"""
Really basic logging config to be used by different modules throughtout Otto. This will need to be worked on as the
project progresses. I have no time to create a sophisticated logger right now
"""

import logging
import colorlog

formatter = colorlog.ColoredFormatter(
    "%(log_color)s[%(asctime)s] %(levelname)s]: %(message)s",
    log_colors={
        'DEBUG': 'green',
        'INFO': 'bold_cyan',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    },
    secondary_log_colors={
        'asctime': {'DEBUG': 'green', 'INFO': 'bold_cyan', 'WARNING': 'yellow', 'ERROR': 'red', 'CRITICAL': 'bold_red'}
    }
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger("otto_logger")

if not logger.hasHandlers():
   logger.addHandler(handler)

logger.setLevel(logging.INFO)


logging.getLogger("requests").setLevel(logging.CRITICAL)
