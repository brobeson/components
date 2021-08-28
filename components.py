"""Generate a component diagram of modules."""


import glob
import os.path
from pprint import pprint


def main() -> None:
    python_files = _get_python_files(".")
    imports = {
        f.replace("/", ".").replace(".py", ""): _get_imports(f) for f in python_files
    }
    modules = imports.keys()
    imports = {
        module: _filter_imports(dependencies, modules)
        for module, dependencies in imports.items()
    }
    # pprint(imports)
    _write_component_diagram(imports)


def _get_python_files(root_path: str) -> list:
    if root_path[-1] != "/":
        root_path = root_path + "/"
    python_files = glob.glob(os.path.join(root_path, "**", "*.py"), recursive=True)
    python_files = [f.replace(root_path, "") for f in python_files]
    python_files = [
        f
        for f in python_files
        if f != os.path.basename(__file__) and not f.endswith("conf.py")
    ]
    return python_files


def _get_imports(python_file: str) -> list:
    with open(python_file, "r") as f:
        lines = [
            line.strip().replace("import ", "")
            for line in f.readlines()
            if line.startswith("import")
        ]
    return lines


def _filter_imports(imports: list, modules: list) -> None:
    local_imports = [i for i in imports if i in modules]
    return local_imports


def _write_component_diagram(modules: dict) -> None:
    with open("component_diagram.puml", "w") as plantuml_file:
        plantuml_file.writelines(["@startuml\n", "skinparam linetype ortho\n"])
        for module, dependencies in modules.items():
            if not module.endswith("__init__") or dependencies:
                plantuml_file.write(f"[{module}]\n")
                for d in dependencies:
                    plantuml_file.write(f"[{module}] --> [{d}]\n")
        plantuml_file.write("@enduml")


if __name__ == "__main__":
    main()
