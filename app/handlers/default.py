import importlib
import logging
from typing import Any, Callable, Type
import os
from pathlib import Path
from inspect import getmembers

import app.routes.responses as responses
from fastapi import FastAPI, HTTPException, Request, Response

from app.handlers.base_handlers import handle_http_exception


# checks which objects are exception mappings
def exc_finder(obj: Any) -> bool:
    return (
        isinstance(obj, tuple)
        and len(obj) == 2
        and issubclass(obj[0], Exception)
        and isinstance(obj[1], HTTPException)
    )


# import all exceptions from app.routes.responses.* with importlib and add default handlers
def add_default_handlers(app: FastAPI) -> None:
    exceptions: list[tuple[str, tuple[Type[Exception], HTTPException]]] = []
    module_path = Path(responses.__file__).parent
    for file_name in os.listdir(module_path):
        if not file_name.endswith(".py") or file_name == "__init__.py":
            continue
        module_name = file_name.rstrip(".py")
        module = importlib.import_module(f"{responses.__package__}.{module_name}")
        for name, val in getmembers(module, exc_finder):
            exceptions.append((name, val))

    logging.debug(f"Installing default exception handlers: {', '.join(e[0] for e in exceptions)}")
    for _, (exc_type, exc_to_throw) in exceptions:
        app.add_exception_handler(exc_type, __get_handler(exc_to_throw))


def __get_handler(exc_to_throw: HTTPException) -> Callable[[Request, Type[Exception]], Response]:
    return lambda req, _: handle_http_exception(req, exc_to_throw)
