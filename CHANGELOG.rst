CHANGELOG
=========

Unreleased
----------

- Add support for Python 3.14
- Remove support for Python 3.8

1.3.1
-----

- Fix a bug in which names in includes were not normalized before comparisons,
  resulting in spurious ``LookupError``\s.
- Optimize the behavior of the ``resolve()`` function on multiple groups.

1.3.0
-----

- Bugfix: raise a ``TypeError`` on non-list groups (was ``ValueError``).
  Thanks :user:`henryiii`!

- Several improvements to the CLI interfaces! Thanks :user:`henryiii`!

  - Add support for a ``cli`` extra, as in
    ``pip install "dependency-groups[cli]"``, which ensures that ``tomli`` is
    present on older Pythons.

  - Add support for ``dependency-groups`` as an entrypoint, as an alias of
    ``python -m dependency_groups``.

  - The ``dependency-groups`` command now supports a ``--list`` flag to list
    groups instead of resolving them.

1.2.0
-----

- Switch to ``flit-core`` as the build backend
- Add support for supplying multiple dependency groups to the functional
  ``resolve()`` API: ``resolve(dependency_groups, *groups: str)``. Thanks
  :user:`henryiii`!

1.1.0
-----

- Add support for Python 3.8

1.0.0
-----

- Update metadata to 1.0.0 and "Production" status
- Support Python 3.13

0.3.0
-----

- Add a new command, ``pip-install-dependency-groups``, which is capable of
  installing dependency groups by invoking ``pip``

0.2.2
-----

- The pre-commit hook sets ``pass_filenames: false``
- The error presentation in the lint CLI has been improved

0.2.1
-----

- Bugfix to pre-commit config

0.2.0
-----

- Add a new CLI component, ``lint-dependency-groups``, which can be used to lint
  dependency groups.
- Provide a pre-commit hook, named ``lint-dependency-groups``

0.1.1
-----

- Fix a bug in cycle detection for nontrivial cycles

0.1.0
-----

- Initial Release
