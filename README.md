# Proteines Resilientes

Global technical diagram of the solution:

![tech-diagram](./docs/tech-diagram.svg)

And the diagram of the relational database model:

![rdb-diagram](./docs/rdb_diagram.svg)

## Installation

This Python project is packaged with [Poetry][poetry].

To install the project dependencies:

    $ poetry install

Poetry installs all the dependencies in a virtual environment. To activate the
environment:

    $ $(poetry env activate)

## Usage

The project is made of multiple CLI tools:

* `pr-offdc`: Proteines Resilientes OpenFoodFacts Data Collector takes a list of
  EANs (product references) as input and fetches the corresponding product data
  from OpenFoodFacts via its REST API.

## Development

### Testing

To run all the tests:

    $ python -m unittest discover

## Documentation

### Generating the Mermaid diagrams

To generate the diagrams made with [mermaid][mermaid]:

    $ npx -p @mermaid-js/mermaid-cli mmdc -i <input> -o <output>

For instance, to generate an SVG image of the relational database diagram:

    $ npx -p @mermaid-js/mermaid-cli mmdc -i docs/rdb_diagram.mermaid -o docs/rdb_diagram.svg

 [mermaid]: http://mermaid.js.org/ "Mermaid website"
 [poetry]: https://python-poetry.org "Poetry website"
