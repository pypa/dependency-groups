from __future__ import annotations

import dataclasses
import re
from collections.abc import Mapping, Sequence

from packaging.requirements import Requirement


def _normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _normalize_group_names(
    dependency_groups: Mapping[str, Sequence[str | Mapping[str, str]]],
) -> tuple[Mapping[str, Sequence[str | Mapping[str, str]]], Mapping[str, str]]:
    """
    Normalize group names and return both normalized groups and reverse mapping.

    Returns a tuple of (normalized_groups, normalized_to_original).
    """
    original_names: dict[str, list[str]] = {}
    normalized_groups: dict[str, Sequence[str | Mapping[str, str]]] = {}
    normalized_to_original: dict[str, str] = {}

    for group_name, value in dependency_groups.items():
        normed_group_name = _normalize_name(group_name)
        original_names.setdefault(normed_group_name, []).append(group_name)
        normalized_groups[normed_group_name] = value
        normalized_to_original[normed_group_name] = group_name

    errors = []
    for normed_name, names in original_names.items():
        if len(names) > 1:
            errors.append(f"{normed_name} ({', '.join(names)})")
    if errors:
        raise ValueError(f"Duplicate dependency group names: {', '.join(errors)}")

    return normalized_groups, normalized_to_original


@dataclasses.dataclass
class DependencyGroupInclude:
    include_group: str


class CyclicDependencyError(ValueError):
    """
    An error representing the detection of a cycle.
    """

    def __init__(self, requested_group: str, group: str, include_group: str) -> None:
        self.requested_group = requested_group
        self.group = group
        self.include_group = include_group

        if include_group == group:
            reason = f"{group} includes itself"
        else:
            reason = f"{include_group} -> {group}, {group} -> {include_group}"
        super().__init__(
            "Cyclic dependency group include while resolving "
            f"{requested_group}: {reason}"
        )


class DependencyGroupResolver:
    """
    A resolver for Dependency Group data.

    This class handles caching, name normalization, cycle detection, and other
    parsing requirements. There are only two public methods for exploring the data:
    ``lookup()`` and ``resolve()``.

    :param dependency_groups: A mapping, as provided via pyproject
        ``[dependency-groups]``.
    """

    def __init__(
        self,
        dependency_groups: Mapping[str, Sequence[str | Mapping[str, str]]],
    ) -> None:
        if not isinstance(dependency_groups, Mapping):
            raise TypeError("Dependency Groups table is not a mapping")
        self.dependency_groups, self._normalized_to_original = _normalize_group_names(
            dependency_groups
        )
        # a map of group names to parsed data
        self._parsed_groups: dict[
            str, tuple[Requirement | DependencyGroupInclude, ...]
        ] = {}
        # a map of group names to their ancestors, used for cycle detection
        self._include_graph_ancestors: dict[str, tuple[str, ...]] = {}
        # a cache of completed resolutions to Requirement lists
        self._resolve_cache: dict[str, tuple[Requirement, ...]] = {}

    def lookup(self, group: str) -> tuple[Requirement | DependencyGroupInclude, ...]:
        """
        Lookup a group name, returning the parsed dependency data for that group.
        This will not resolve includes.

        :param group: the name of the group to lookup

        :raises ValueError: if the data does not appear to be valid dependency group
            data
        :raises TypeError: if the data is not a string
        :raises LookupError: if group name is absent
        :raises packaging.requirements.InvalidRequirement: if a specifier is not valid
        """
        if not isinstance(group, str):
            raise TypeError("Dependency group name is not a str")
        group = _normalize_name(group)
        return self._parse_group(group)

    def resolve(self, group: str) -> tuple[Requirement, ...]:
        """
        Resolve a dependency group to a list of requirements.

        :param group: the name of the group to resolve

        :raises TypeError: if the inputs appear to be the wrong types
        :raises ValueError: if the data does not appear to be valid dependency group
            data
        :raises LookupError: if group name is absent
        :raises packaging.requirements.InvalidRequirement: if a specifier is not valid
        """
        if not isinstance(group, str):
            raise TypeError("Dependency group name is not a str")
        group = _normalize_name(group)
        return self._resolve(group, group)

    def _parse_group(
        self, group: str
    ) -> tuple[Requirement | DependencyGroupInclude, ...]:
        # short circuit -- never do the work twice
        if group in self._parsed_groups:
            return self._parsed_groups[group]

        if group not in self.dependency_groups:
            raise LookupError(f"Dependency group '{group}' not found")

        raw_group = self.dependency_groups[group]
        if isinstance(raw_group, str):
            raise TypeError(
                f"Dependency group '{group}' contained a string rather than a sequence."
            )
        if not isinstance(raw_group, Sequence):
            raise TypeError(f"Dependency group '{group}' is not a sequence")

        elements: list[Requirement | DependencyGroupInclude] = []
        for item in raw_group:
            if isinstance(item, str):
                # packaging.requirements.Requirement parsing ensures that this is a
                # valid PEP 508 Dependency Specifier
                # raises InvalidRequirement on failure
                elements.append(Requirement(item))
            elif isinstance(item, Mapping):
                if tuple(item.keys()) != ("include-group",):
                    raise ValueError(f"Invalid dependency group item: {item}")

                include_group = next(iter(item.values()))
                if not isinstance(include_group, str):
                    raise ValueError(f"Invalid dependency group item: {item}")
                elements.append(DependencyGroupInclude(include_group=include_group))
            else:
                raise ValueError(f"Invalid dependency group item: {item}")

        self._parsed_groups[group] = tuple(elements)
        return self._parsed_groups[group]

    def _resolve(self, group: str, requested_group: str) -> tuple[Requirement, ...]:
        """
        This is a helper for cached resolution to strings.

        :param group: The name of the group to resolve.
        :param requested_group: The group which was used in the original, user-facing
            request.
        """
        if group in self._resolve_cache:
            return self._resolve_cache[group]

        parsed = self._parse_group(group)

        resolved_group = []
        for item in parsed:
            if isinstance(item, Requirement):
                resolved_group.append(item)
            elif isinstance(item, DependencyGroupInclude):
                include_group = _normalize_name(item.include_group)
                if include_group in self._include_graph_ancestors.get(group, ()):
                    raise CyclicDependencyError(
                        requested_group, group, item.include_group
                    )
                self._include_graph_ancestors[include_group] = (
                    *self._include_graph_ancestors.get(group, ()),
                    group,
                )
                resolved_group.extend(self._resolve(include_group, requested_group))
            else:  # unreachable
                raise NotImplementedError(
                    f"Invalid dependency group item after parse: {item}"
                )

        self._resolve_cache[group] = tuple(resolved_group)
        return self._resolve_cache[group]

    def resolve_all(self) -> Mapping[str, tuple[Requirement, ...]]:
        """
        Resolve all dependency groups, returning a mapping of normalized group
        names to resolved requirements.

        This is more efficient than calling resolve() on each group individually
        because it avoids repeated work when groups share common includes.

        :raises TypeError: if the data appears to be the wrong types
        :raises ValueError: if the data does not appear to be valid dependency group
            data
        :raises packaging.requirements.InvalidRequirement: if a specifier is not valid
        """
        # Resolve all groups that haven't been resolved yet
        for group in self.dependency_groups:
            self._resolve(group, group)

        return dict(self._resolve_cache)


def resolve(
    dependency_groups: Mapping[str, Sequence[str | Mapping[str, str]]], /, *groups: str
) -> tuple[str, ...]:
    """
    Resolve a dependency group to a tuple of requirements, as strings.

    :param dependency_groups: the parsed contents of the ``[dependency-groups]`` table
        from ``pyproject.toml``
    :param groups: the name of the group(s) to resolve

    :raises TypeError: if the inputs appear to be the wrong types
    :raises ValueError: if the data does not appear to be valid dependency group data
    :raises LookupError: if group name is absent
    :raises packaging.requirements.InvalidRequirement: if a specifier is not valid
    """
    resolver = DependencyGroupResolver(dependency_groups)
    return tuple(str(r) for group in groups for r in resolver.resolve(group))


def resolve_all(
    dependency_groups: Mapping[str, Sequence[str | Mapping[str, str]]],
    /,
    *,
    normalize: bool = False,
) -> Mapping[str, tuple[str, ...]]:
    """
    Resolve all dependency groups, returning a mapping of group names to
    resolved requirements.

    :param dependency_groups: the parsed contents of the ``[dependency-groups]`` table
        from ``pyproject.toml``
    :param normalize: if True normalize names, otherwise use original names
        when returning keys, but still normalize for lookup. Defaults to False.

    :raises TypeError: if the inputs appear to be the wrong types
    :raises ValueError: if the data does not appear to be valid dependency group data
    :raises packaging.requirements.InvalidRequirement: if a specifier is not valid

    Example usage::

        resolved = dependency_groups.resolve_all(dep_groups)
        # {'test': ('pytest', 'sqlalchemy'), 'runtime': ('sqlalchemy',)}
    """
    resolver = DependencyGroupResolver(dependency_groups)
    resolved = resolver.resolve_all()
    if normalize:
        return {
            group: tuple(str(r) for r in requirements)
            for group, requirements in resolved.items()
        }
    else:
        # Map back to original names
        return {
            resolver._normalized_to_original.get(group, group): tuple(
                str(r) for r in requirements
            )
            for group, requirements in resolved.items()
        }
