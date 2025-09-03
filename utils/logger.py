import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler
from rich.console import Console
from datetime import datetime
import re
from collections import Counter


class NonRepetitiveLogger(logging.Logger):
    """
    Logger personalizzato che filtra messaggi duplicati basati sull'hash del contenuto.
    """
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name=name, level=level)
        self._dedup_cache = set()
        self.propagate = False

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False):
        h = hash(msg)
        if h in self._dedup_cache:
            return
        self._dedup_cache.add(h)
        super()._log(level, msg, args, exc_info, extra, stack_info)


# Override del logger base
logging.setLoggerClass(NonRepetitiveLogger)


def get_logger(name: str = "crew_logger", level: str = "INFO", log_to_file: bool = True) -> logging.Logger:
    """
    Costruisce un logger configurato con RichHandler e RotatingFileHandler.
    """
    LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    console = Console()
    handlers = [RichHandler(console=console, rich_tracebacks=True, markup=True, show_time=False)]

    if log_to_file:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_path = log_dir / f"{name}.log"
        file_handler = RotatingFileHandler(
            filename=file_path,
            maxBytes=2 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        handlers.append(file_handler)

    logger = logging.getLogger(name)
    if not logger.handlers:
        for h in handlers:
            logger.addHandler(h)

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Silenzia log esterni troppo rumorosi
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    return logger


def summarize_log_metrics(log_path: str) -> dict:
    """
    Analizza un file di log e restituisce un dizionario con statistiche sintetiche.
    """
    levels = Counter()
    timestamps = []
    flow_transitions = Counter()
    messages = []

    level_pattern = re.compile(r"\|\s+(INFO|WARNING|ERROR|DEBUG)\s+\|")
    transition_pattern = re.compile(r"→\s*(\w+)")

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                messages.append(line.strip())

                # Conta i livelli
                level_match = level_pattern.search(line)
                if level_match:
                    levels[level_match.group(1)] += 1

                # Estrai timestamp
                try:
                    timestamp = datetime.strptime(line[:19], "%Y-%m-%d %H:%M:%S")
                    timestamps.append(timestamp)
                except Exception:
                    pass

                # Transizioni di stato nel flow
                transition_match = transition_pattern.search(line)
                if transition_match:
                    flow_transitions[transition_match.group(1)] += 1

        return {
            "log_lines": len(messages),
            "log_levels": dict(levels),
            "transitions": dict(flow_transitions),
            "duration_seconds": (max(timestamps) - min(timestamps)).total_seconds() if timestamps else 0,
            "first_entry": str(min(timestamps)) if timestamps else None,
            "last_entry": str(max(timestamps)) if timestamps else None,
            "top_messages": Counter(messages).most_common(5)
        }

    except FileNotFoundError:
        return {"error": f"File non trovato: {log_path}"}
    except Exception as e:
        return {"error": str(e)}
