from pathlib import Path

from gouge.colourcli import Simple
from gouge.preformatters import uvicorn_access


class LogFormatter(Simple):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            pre_formatters={
                "uvicorn.access": [uvicorn_access],
            },
            show_exc=True,
            highlighted_path=Path("powonline"),
            **kwargs,
        )
