import importlib
import pkgutil
from aiogram import Router
from pathlib import Path

routers_path = Path(__file__).parent
__all__ = []

all_routers = []

# Автоматически импортировать все роутеры из файлов routers/*.py
for _, module_name, _ in pkgutil.iter_modules([str(routers_path)]):
    if module_name.startswith("_") or not module_name.endswith("_router"):
        continue
    module = importlib.import_module(f"routers.{module_name}")
    for attr in dir(module):
        obj = getattr(module, attr)
        if isinstance(obj, Router):
            all_routers.append(obj)
            __all__.append(attr)
