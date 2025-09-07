"""Module entry point to support `python -m quickcapture`.
Sets up basic logging and dispatches to CLI.
"""
import logging
from .cli import main


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


if __name__ == "__main__":  # pragma: no cover
    _setup_logging()
    main()
