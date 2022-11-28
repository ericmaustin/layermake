import sys
from rich.console import Console
from typing import Any


class _Logger:
    """ global context object to be initialized at beginning of program with set_ctx()"""

    def __init__(self, verbose: bool):
        self._verbose = verbose
        self._rc = Console(
            log_path=False,
            log_time_format="[%X.%f] "
        )

    @property
    def verbose(self):
        return self._verbose

    def status(self, status_text: str, log_text: bool = False, **kwargs):
        if log_text:
            self.log(status_text)
        return self._rc.status(status_text, **kwargs)

    def fatal_error(self, msg: str, **kwargs):
        self._rc.log(f'[bold red]{msg}', **kwargs)
        sys.exit(1)

    def log(self, *objects: Any, **kwargs):
        self._rc.log(*objects, **kwargs)

    def error(self, msg: Any, **kwargs):
        self._rc.log(f'[red]{msg}', **kwargs)

    def success(self, msg: Any, **kwargs):
        self._rc.log(f'[green]{msg}', **kwargs)

    def warn(self, msg: Any, **kwargs):
        self._rc.log(f'[orange]{msg}', **kwargs)

    def debug(self, *objects: Any, **kwargs):
        if self.verbose:
            self.log(*objects, **kwargs)


# singleton
_logger = None


def set_logger(verbose: bool):
    global _logger
    if verbose:
        print('verbose output enabled')
    _logger = _Logger(verbose)


def logger() -> _Logger:
    assert _logger
    return _logger
