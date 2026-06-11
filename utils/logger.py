"""
utils/logger.py — Logger centralizado
"""

import logging
from utils.banner import Colors


class ColoredFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG:    Colors.DIM    + "[DEBUG] %(message)s" + Colors.RESET,
        logging.INFO:     Colors.CYAN   + "[*] %(message)s"     + Colors.RESET,
        logging.WARNING:  Colors.YELLOW + "[!] %(message)s"     + Colors.RESET,
        logging.ERROR:    Colors.RED    + "[-] %(message)s"     + Colors.RESET,
        logging.CRITICAL: Colors.RED    + Colors.BOLD + "[!!] %(message)s" + Colors.RESET,
    }

    def format(self, record):
        fmt = self.FORMATS.get(record.levelno, "%(message)s")
        formatter = logging.Formatter(fmt)
        return formatter.format(record)


def get_logger(name="osint"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(ColoredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
