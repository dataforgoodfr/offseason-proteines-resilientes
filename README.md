# Proteines Resilientes

![tech-diagram](./docs/tech-diagram.svg)

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

## Testing

To run all the tests:

    $ python -m unittest discover

 [poetry]: https://python-poetry.org "Poetry website"
