# Proteines Resilientes

Proteines Resilientes is a data study designed to gather information from
various online sources about food products sold in France, particularly their
nutritional facts. The project's primary objective is to compare plant-based and
animal-based products to assess their affordability, protein content, and other
relevant factors.

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

### Database Migrations

[Alembic][alembic] is used to manage the database migrations. It is part of the
development dependencies of the project that are automatically installed when
running `poetry install`.

When updating the database schema in `./src/models`, Alembic can automatically
detect drifts between the models and the current state of the actually database,
and then generate migration scripts:

    $ alembic revision --autogenerate -m "Migration description..."

A new migration script will be added to `./migrations/versions`. As some schema
drifts cannot be automatically detected by Alembic (e.g. change of table name),
the migration commands need to be reviewed and adjusted if necessary.

More information on the auto-generated migration scripts can be found in the
[Alembic official documentation][alembic-autogenerate].

To apply the migration scripts to the latest available revision:

    $ alembic upgrade head

## Documentation

### Generating the Mermaid diagrams

To generate the diagrams made with [mermaid][mermaid]:

    $ npx -p @mermaid-js/mermaid-cli mmdc -i <input> -o <output>

For instance, to generate an SVG image of the relational database diagram:

    $ npx -p @mermaid-js/mermaid-cli mmdc -i docs/rdb_diagram.mermaid -o docs/rdb_diagram.svg

 [alembic]: https://alembic.sqlalchemy.org "Alembic documentation website"
 [alembic-autogenerate]: https://alembic.sqlalchemy.org/en/latest/autogenerate.html "Auto Generating Migrations - Alembic documentation"
 [mermaid]: http://mermaid.js.org/ "Mermaid website"
 [poetry]: https://python-poetry.org "Poetry website"
