import sys
from rich.console import Console
from typing import Any


class QuietStatus:
    """ stub class used to replace rich console Status when in quiet mode"""

    def __init__(*args, **kwargs):
        pass

    def update(*args, **kwargs) -> None:
        pass

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(*args, **kwargs) -> None:
        pass


class _Logger:
    """ global context object to be initialized at beginning of program with set_ctx()"""

    def __init__(self, verbose: bool, quiet: bool):
        self._verbose = verbose
        self._quiet = quiet
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

        if self._quiet:
            return QuietStatus()

        return self._rc.status(status_text, **kwargs)

    def fatal_error(self, msg: str, **kwargs):
        self._rc.log(f'[bold red]{msg}', **kwargs)
        sys.exit(1)

    def log(self, *objects: Any, **kwargs):
        if not self._quiet:
            self._rc.log(*objects, **kwargs)

    def error(self, msg: Any, **kwargs):
        self._rc.log(f'[red]{msg}', **kwargs)

    def success(self, msg: Any, **kwargs):
        if not self._quiet:
            self._rc.log(f'[green]{msg}', **kwargs)

    def warn(self, msg: Any, **kwargs):
        self._rc.log(f'[orange]{msg}', **kwargs)

    def debug(self, *objects: Any, **kwargs):
        if self.verbose and not self._quiet:
            self.log(*objects, **kwargs)


# singleton
_logger = None


def set_logger(verbose: bool, quiet: bool):
    global _logger
    if verbose:
        print('verbose output enabled')
    _logger = _Logger(verbose, quiet)


def logger() -> _Logger:
    assert _logger
    return _logger
