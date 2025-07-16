from __future__ import annotations

from dotenv import load_dotenv
from typer import Typer

cli = Typer(no_args_is_help=True, add_completion=False)

@cli.command()
def run() -> None:
    load_dotenv()
    print("Hello Swipe!")