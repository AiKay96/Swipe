from __future__ import annotations

import uvicorn
from dotenv import load_dotenv
from typer import Typer

from src.runner.setup import init_app

cli = Typer(no_args_is_help=True, add_completion=False)


@cli.command()
def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    load_dotenv()
    uvicorn.run(app=init_app(), host=host, port=port)
