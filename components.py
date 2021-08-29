"""Generate a component diagram of modules."""


import argparse
import glob
import os.path
from pprint import pprint
import re
import sys


def main() -> None:
    arguments = _parse_command_line()
    python_files = _get_python_files(arguments.project)
    modules = [
        _Module(_path_to_module_name(f, arguments.project), f) for f in python_files
    ]
    module_names = [m.name for m in modules]
    for module in modules:
        module.dependencies = _filter_imports(_get_imports(module.path), module_names)
    _write_component_diagram(modules)


class _Module:
    def __init__(self, name: str, path: str, dependencies: list = None) -> None:
        self.name = name
        self.path = path
        self.dependencies = [] if dependencies is None else dependencies

    def __str__(self):
        return f"{self.name}\n  {self.path}\n  " + (
            ",".join(self.dependencies) if self.dependencies else "<no dependencies>"
        )

    def __repr__(self) -> str:
        return str(self)


def _parse_command_line() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a dependency graph for a Python project.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "project",
        help="The path to the Python project.",
        default=".",
    )
    arguments = parser.parse_args()
    arguments.project = os.path.abspath(os.path.expanduser(arguments.project))
    if arguments.project[-1] != "/":
        arguments.project = arguments.project + "/"
    return arguments


def _path_to_module_name(path: str, root_path: str) -> str:
    return path.replace(root_path, "").replace(".py", "").replace("/", ".")


def _get_python_files(root_path: str) -> list:
    if root_path[-1] != "/":
        root_path = root_path + "/"
    python_files = glob.glob(os.path.join(root_path, "**", "*.py"), recursive=True)
    python_files = [
        f
        for f in python_files
        if f != os.path.basename(__file__) and not f.endswith("conf.py")
    ]
    return python_files


def _get_imports(python_file: str) -> list:
    as_expression = re.compile(r"\s+as.*$")
    with open(python_file, "r") as f:
        lines = [
            re.sub(as_expression, "", line.strip().replace("import ", ""))
            for line in f.readlines()
            if line.startswith("import")
        ]
    return lines


def _filter_imports(imports: list, modules: list) -> None:
    local_imports = [i for i in imports if i in modules]
    return local_imports


def _write_component_diagram(modules: list) -> None:
    with open("component_diagram.puml", "w") as plantuml_file:
        plantuml_file.writelines(["@startuml\n", "skinparam linetype ortho\n"])
        for module in modules:
            if not module.name.endswith("__init__") or module.dependencies:
                plantuml_file.write(f"[{module.name}]\n")
                for d in module.dependencies:
                    plantuml_file.write(f"[{module.name}] --> [{d}]\n")
        plantuml_file.write("@enduml")


if __name__ == "__main__":
    main()
