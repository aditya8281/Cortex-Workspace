import importlib
import pkgutil
from inspect import signature

from backend.app.tools.base import BaseTool


def discover_tools(package) -> list[BaseTool]:

    tools = []

    for _, module_name, _ in pkgutil.iter_modules(package.__path__):

        module = importlib.import_module(f"{package.__name__}.{module_name}")

        for attr in dir(module):
            obj = getattr(module, attr)

            if (
                isinstance(obj, type)
                and issubclass(obj, BaseTool)
                and obj is not BaseTool
            ):
                try:
                    init_params = signature(obj.__init__).parameters
                    required_args = [
                        name
                        for name, param in init_params.items()
                        if name != "self"
                        and param.default is param.empty
                    ]

                    if required_args:
                        continue

                    tools.append(obj())

                except (TypeError, ValueError):
                    continue

    return tools
