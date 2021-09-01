Components is a tool to generate a dependency graph between the modules of a Python project.
It reads the Python files and generates a UML component diagram using [PlantUML](https://plantuml.com) syntax.

There some caveats with this software:

- The diagram omits dependencies on 3rd party packages including the Python standard library.
- This is still alpha software, so it *might* miss a dependency.
  If this occurs, it's likely because I overlooked a way of importing a module.

## Installing Components

Download *components.py*.

```bash
wget components.py
```

## Using Components

Run the module via Python.
It has one required argument: the path to your Python project.

```bash
python3 -m components path/to/your/project
```

### Output

By default, components writes the PlantUML text to standard output.
You can tell it to write the output to a file instead:

```bash
python3 -m components --output-file graph.puml path/to/your/project
```

You can also tell components to run PlantUML and generate the diagram image.
This option requires that you [install PlantUML](https://plantuml.com/starting) and have a script in your `PATH` called `plantuml`.

```bash
python3 -m components \
  --output-file graph.puml \
  --image-type png \
  path/to/your/project
```

You must also use `--output-file`; components will print an error if you forget.
The image has the same filename as your `--output-file`, but with the extension appropriate for your `--image-type`, and in the same location as your `--output-file`.
For example, if you run

```bash
$ python3 -m components \
  --output-file ~/diagrams/numpy_dependenies.puml \
  --image-type svg \
  ~/projects/numpy
```

then components will produce two files: *~/diagrams/numpy_dependencies.puml* and *~/diagrams/numpy_dependencies.svg*.
