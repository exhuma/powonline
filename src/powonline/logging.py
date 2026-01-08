from pathlib import Path
from typing import Any

from gouge.colourcli import Simple
from gouge.preformatters import uvicorn_access


class LogFormatter(Simple):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(
            *args,
            pre_formatters={
                "uvicorn.access": [uvicorn_access],
            },
            show_exc=True,
            highlighted_path=Path("powonline"),
            **kwargs,
        )
