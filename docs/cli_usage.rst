CLI Usage
=========

There are three CLI tools provided by ``dependency-groups``.

Viewing Groups
--------------

``dependency-groups`` is a CLI command, provided by the package.
It can parse a pyproject.toml file and print a dependency group's contents back
out, newline separated.
This data is therefore valid for use as a ``requirements.txt`` file.

``dependency-groups --list`` can be used to list the available dependency
groups.

Use ``dependency-groups --help`` for details!


Module Usage
^^^^^^^^^^^^

``dependency-groups`` provides a module-level entrypoint, identical to the
``dependency-groups`` CLI.

e.g., ``python -m dependency_groups --list`` can be used to list groups.

Installer
---------

``dependency-groups`` includes a ``pip`` wrapper, ``pip-install-dependency-groups``.

Usage is simple, just ``pip-install-dependency-groups groupname`` to install!

Use ``pip-install-dependency-groups --help`` for more details.

Linter
------

``dependency-groups`` includes a linter, ``lint-dependency-groups``, as a separate
CLI entrypoint.

Use ``lint-dependency-groups --help`` for details.

The ``lint-dependency-groups`` CLI is also available as a pre-commit hook:

.. code-block:: yaml

    repos:
      - repo: https://github.com/pypa/dependency-groups
        rev: 1.3.0
        hooks:
          - id: lint-dependency-groups
