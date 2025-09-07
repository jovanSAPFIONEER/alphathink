"""Optional module runner.

Kept for convenience; `python -m quickcapture` uses `__main__.py`.
"""
from .cli import main as cli_main


def main() -> None:  # pragma: no cover
    cli_main()


if __name__ == "__main__":  # pragma: no cover
    main()
