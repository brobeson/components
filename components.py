"""Generate a component diagram of modules."""


import argparse
import glob
import os.path
from pprint import pprint
import re


def main() -> None:
    arguments = _parse_command_line()
    python_files = _get_python_files(arguments.project)
    modules = [
        _Module(_path_to_module_name(f, arguments.project), f) for f in python_files
    ]
    module_names = [m.full_name for m in modules]
    for module in modules:
        module.dependencies = _filter_imports(_get_imports(module), module_names)
    modules = [module for module in modules if _include_module(module)]
    _write_component_diagram(modules)


class _Module:
    """
    Encapsulates the data about a module in the Python project.

    Attributes:
        full_name (str): The fully qualified name of the module, like ``package.package.module``.
        path (str): The path to the module on disk.
        dependencies (list): The list of modules that this module imports.
    """

    def __init__(self, name: str, path: str, dependencies: list = None) -> None:
        self.full_name = name
        self.path = path
        self.dependencies = [] if dependencies is None else dependencies
        split_name = name.split(".")
        self.packages = split_name[:-1]
        self.name = split_name[-1]

    def __str__(self):
        return f"{self.full_name}\n  {self.path}\n  " + (
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
        "project", help="The path to the Python project.", default=".",
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


def _get_imports(module: _Module) -> list:
    import_expression = re.compile(r"^(?:import|from)\s+([^\s]+)")
    with open(module.path, "r") as f:
        lines = [
            line
            for line in f.readlines()
            if line.startswith("import ") or line.startswith("from ")
        ]
    imports = []
    for line in lines:
        match = import_expression.match(line)
        if match:
            imports.append(match[1])
    imports = [i[1:] if i.startswith(".") else i for i in imports]
    imports = _match_local_modules(imports, module)
    return imports


def _match_local_modules(imports: list, module: _Module) -> list:
    """
    Match a module's imports to modules in the same directory.

    Args:
        imports (list): The list of modules imported by another module.
        module (_Module): The importing module.

    Returns:
        list: The list of ``imports``, with sibling modules updated with full names.
    """
    module_directory = os.path.dirname(module.path)
    return [
        ".".join(module.packages) + "." + imported_module
        if os.path.exists(os.path.join(module_directory, f"{imported_module}.py"))
        else imported_module
        for imported_module in imports
    ]


def _filter_imports(imports: list, modules: list) -> None:
    local_imports = list({i for i in imports if i in modules})
    return local_imports


def _write_component_diagram(modules: list) -> None:
    with open("component_diagram.puml", "w") as plantuml_file:
        plantuml_file.writelines(["@startuml\n", "skinparam linetype ortho\n"])
        _write_module_to_diagram(modules, plantuml_file)
        _write_dependencies_to_diagram(modules, plantuml_file)
        plantuml_file.write("@enduml")


def _write_module_to_diagram(modules: list, plantuml_file) -> None:
    for module in modules:
        for i, package in enumerate(module.packages):
            plantuml_file.write(
                f"frame {package} as {'.'.join(module.packages[:i+1])} {{\n"
            )
        plantuml_file.write(f"[{module.name}] as {module.full_name}\n")
        for package in module.packages:
            plantuml_file.write("}\n")


def _write_dependencies_to_diagram(modules: list, plantuml_file) -> None:
    for module in modules:
        for d in module.dependencies:
            plantuml_file.write(f"[{module.full_name}] --> [{d}]\n")


def _include_module(module: _Module) -> None:
    return module.name != "__init__" or module.dependencies


if __name__ == "__main__":
    main()
