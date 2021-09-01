"""Generate a component diagram of modules."""


import argparse
import glob
import os.path
import re
import subprocess
import sys


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
    if arguments.output_file:
        with open(arguments.output_file, "w") as plantuml_file:
            _write_component_diagram(modules, plantuml_file)
    else:
        _write_component_diagram(modules, sys.stdout)
    if arguments.image_type:
        _run_plantuml(arguments.output_file, arguments.image_type)


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
        "--output-file",
        help="Write the PlantUML text to this file. If you omit this, the application writes the "
        "PlantUML text to standard output.",
    )
    parser.add_argument(
        "--image-type",
        help="Run PlantUML and write an image of this type. See the PlantUML documentation for "
        "a list of acceptable types (https://plantuml.com/command-line#458de91d76a8569c). You just "
        "need to use the format acronym, such as '--image-type=png' or '--image-type=scxml'. This "
        "option requires --output-file.",
    )
    parser.add_argument(
        "project", help="The path to the Python project.", default=".",
    )
    arguments = parser.parse_args()
    if arguments.output_file:
        arguments.output_file = os.path.abspath(
            os.path.expanduser(arguments.output_file)
        )
    if arguments.image_type:
        if not arguments.output_file:
            sys.exit("Using --image-type requires also using --output-file.")
        arguments.image_type = arguments.image_type.lower()
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


def _write_component_diagram(modules: list, plantuml_file) -> None:
    """
    Write the PlantUML file.

    Args:
        modules (list): The list of Python modules to include in the diagram.
        plantuml_file: The destination stream for the PlantUML code. This should be an open file
            stream, or a system stream such as ``sys.stdout``.
    """
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


def _run_plantuml(plantuml_file: str, image_type: str) -> None:
    """
    Run PlantUML to generate the final diagram.

    Arguments:
        plantuml_file (str): The path to the input file for PlantUML.
        image_type (str): The type of image for PlantUML to generate.
    """
    subprocess.run(
        [
            "plantuml",
            "-t" + image_type,
            "-output",
            os.path.dirname(plantuml_file),
            plantuml_file,
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
