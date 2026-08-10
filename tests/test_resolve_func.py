from __future__ import annotations

import typing as t

import pytest

from dependency_groups import resolve, resolve_all

if t.TYPE_CHECKING:
    from conftest import Groups


def test_empty_group() -> None:
    groups: Groups = {"test": []}
    assert resolve(groups, "test") == ()


def test_str_list_group() -> None:
    groups = {"test": ["pytest"]}
    assert resolve(groups, "test") == ("pytest",)


def test_single_include_group() -> None:
    groups: Groups = {
        "test": [
            "pytest",
            {"include-group": "runtime"},
        ],
        "runtime": ["sqlalchemy"],
    }
    assert set(resolve(groups, "test")) == {"pytest", "sqlalchemy"}


def test_sdual_include_group() -> None:
    groups = {
        "test": [
            "pytest",
        ],
        "runtime": ["sqlalchemy"],
    }
    assert set(resolve(groups, "test", "runtime")) == {"pytest", "sqlalchemy"}


def test_normalized_group_name() -> None:
    groups = {
        "TEST": ["pytest"],
    }
    assert resolve(groups, "test") == ("pytest",)


def test_malformed_group_data() -> None:
    groups: t.Any = [{"test": ["pytest"]}]
    with pytest.raises(TypeError, match="Dependency Groups table is not a mapping"):
        resolve(groups, "test")


def test_malformed_group_query() -> None:
    groups = {"test": ["pytest"]}
    with pytest.raises(TypeError, match="Dependency group name is not a str"):
        resolve(groups, 0)  # type: ignore[arg-type]


def test_no_such_group_name() -> None:
    groups = {
        "test": ["pytest"],
    }
    with pytest.raises(LookupError, match="'testing' not found"):
        resolve(groups, "testing")


def test_duplicate_normalized_name() -> None:
    groups = {
        "test": ["pytest"],
        "TEST": ["nose2"],
    }
    with pytest.raises(
        ValueError,
        match=r"Duplicate dependency group names: test \((test, TEST)|(TEST, test)\)",
    ):
        resolve(groups, "test")


def test_cyclic_include() -> None:
    groups: Groups = {
        "group1": [
            {"include-group": "group2"},
        ],
        "group2": [
            {"include-group": "group1"},
        ],
    }
    with pytest.raises(
        ValueError,
        match=(
            "Cyclic dependency group include while resolving group1: "
            "group1 -> group2, group2 -> group1"
        ),
    ):
        resolve(groups, "group1")


def test_cyclic_include_many_steps() -> None:
    groups: Groups = {}
    for i in range(100):
        groups[f"group{i}"] = [{"include-group": f"group{i + 1}"}]
    groups["group100"] = [{"include-group": "group0"}]
    with pytest.raises(
        ValueError,
        match="Cyclic dependency group include while resolving group0:",
    ):
        resolve(groups, "group0")


def test_cyclic_include_self() -> None:
    groups: Groups = {
        "group1": [
            {"include-group": "group1"},
        ],
    }
    with pytest.raises(
        ValueError,
        match=(
            "Cyclic dependency group include while resolving group1: "
            "group1 includes itself"
        ),
    ):
        resolve(groups, "group1")


def test_cyclic_include_ring_under_root() -> None:
    groups: Groups = {
        "root": [
            {"include-group": "group1"},
        ],
        "group1": [
            {"include-group": "group2"},
        ],
        "group2": [
            {"include-group": "group1"},
        ],
    }
    with pytest.raises(
        ValueError,
        match=(
            "Cyclic dependency group include while resolving root: "
            "group1 -> group2, group2 -> group1"
        ),
    ):
        resolve(groups, "root")


def test_non_list_data() -> None:
    groups: t.Any = {"test": "pytest, coverage"}
    with pytest.raises(
        TypeError,
        match="Dependency group 'test' contained a string rather than a sequence.",
    ):
        resolve(groups, "test")


@pytest.mark.parametrize(
    "item",
    (
        {},
        {"foo": "bar"},
        {"include-group": "testing", "foo": "bar"},
        object(),
    ),
)
def test_unknown_object_shape(item: object) -> None:
    groups: t.Any = {"test": [item]}
    with pytest.raises(ValueError, match="Invalid dependency group item:"):
        resolve(groups, "test")


def test_non_str_include_group_value() -> None:
    groups: t.Any = {"test": [{"include-group": 5}]}
    with pytest.raises(
        TypeError, match="Invalid include-group value, must be a string:"
    ):
        resolve(groups, "test")


def test_mapping_include_group_item() -> None:
    import types

    groups: Groups = {
        "test": [
            "pytest",
            types.MappingProxyType({"include-group": "runtime"}),
        ],
        "runtime": ["sqlalchemy"],
    }
    assert set(resolve(groups, "test")) == {"pytest", "sqlalchemy"}


def test_resolve_all_empty() -> None:
    groups: Groups = {}
    assert resolve_all(groups) == {}


def test_resolve_all_single_group() -> None:
    groups = {"test": ["pytest"]}
    assert resolve_all(groups) == {"test": ("pytest",)}


def test_resolve_all_multiple_groups() -> None:
    groups: Groups = {
        "test": ["pytest", {"include-group": "runtime"}],
        "runtime": ["sqlalchemy"],
    }
    result = resolve_all(groups)
    assert "test" in result
    assert "runtime" in result
    assert set(result["test"]) == {"pytest", "sqlalchemy"}
    assert result["runtime"] == ("sqlalchemy",)


def test_resolve_all_with_normalize_false() -> None:
    groups = {
        "TEST": ["pytest"],
    }
    result = resolve_all(groups, normalize=False)
    assert "TEST" in result
    assert result["TEST"] == ("pytest",)


def test_resolve_all_with_normalize_true() -> None:
    groups = {
        "TEST": ["pytest"],
    }
    result = resolve_all(groups, normalize=True)
    assert "test" in result
    assert result["test"] == ("pytest",)


def test_resolve_all_default_preserves_names() -> None:
    """Test that normalize=False is the default."""
    groups = {
        "TEST": ["pytest"],
    }
    result = resolve_all(groups)
    assert "TEST" in result
    assert "test" not in result
    assert result["TEST"] == ("pytest",)


def test_resolve_all_shared_includes() -> None:
    """Test that resolve_all correctly handles groups with shared includes.

    Structure:
        dev = [{include-group = "test"}, {include-group = "lint"}]
        test = [{include-group = "pytest"}, {include-group = "coverage"}]
        lint = ["prek", {include-group = "typing"}]
        typing = ["mypy"]
        pytest = ["pytest>=7"]
        coverage = ["coverage[toml]"]
    """
    groups: Groups = {
        "dev": [{"include-group": "test"}, {"include-group": "lint"}],
        "test": [{"include-group": "pytest"}, {"include-group": "coverage"}],
        "lint": ["prek", {"include-group": "typing"}],
        "typing": ["mypy"],
        "pytest": ["pytest>=7"],
        "coverage": ["coverage[toml]"],
    }

    result = resolve_all(groups)

    # Verify all groups are present
    assert set(result.keys()) == {"dev", "test", "lint", "typing", "pytest", "coverage"}

    # Verify each group has correct contents
    assert set(result["typing"]) == {"mypy"}
    assert set(result["pytest"]) == {"pytest>=7"}
    assert set(result["coverage"]) == {"coverage[toml]"}
    assert set(result["lint"]) == {"prek", "mypy"}
    assert set(result["test"]) == {"pytest>=7", "coverage[toml]"}
    assert set(result["dev"]) == {"pytest>=7", "coverage[toml]", "prek", "mypy"}


def test_resolve_all_uses_cache() -> None:
    """Test that resolve_all uses the resolver's internal cache properly.

    This tests that calling resolve_all uses the optimized resolve_all method
    which avoids duplicate work when groups share includes.
    """
    from dependency_groups._implementation import DependencyGroupResolver

    groups: Groups = {
        "dev": [{"include-group": "test"}, {"include-group": "lint"}],
        "test": [{"include-group": "pytest"}, {"include-group": "coverage"}],
        "lint": ["prek", {"include-group": "typing"}],
        "typing": ["mypy"],
        "pytest": ["pytest>=7"],
        "coverage": ["coverage[toml]"],
    }

    # Create a resolver and check that resolve_all populates the cache
    resolver = DependencyGroupResolver(groups)
    assert len(resolver._resolve_cache) == 0

    resolved = resolver.resolve_all()

    # All groups should now be in the cache
    assert len(resolver._resolve_cache) == len(groups)
    for group in resolver.dependency_groups:
        assert group in resolver._resolve_cache

    # Verify the results are correct (resolve_all returns Requirement objects)
    assert {str(r) for r in resolved["dev"]} == {
        "pytest>=7",
        "coverage[toml]",
        "prek",
        "mypy",
    }
    assert {str(r) for r in resolved["test"]} == {"pytest>=7", "coverage[toml]"}
    assert {str(r) for r in resolved["lint"]} == {"prek", "mypy"}


def test_resolve_all_vs_individual_resolve() -> None:
    """Test that resolve_all produces the same results as individual resolve calls."""
    groups: Groups = {
        "dev": [{"include-group": "test"}, {"include-group": "lint"}],
        "test": [{"include-group": "pytest"}, {"include-group": "coverage"}],
        "lint": ["prek", {"include-group": "typing"}],
        "typing": ["mypy"],
        "pytest": ["pytest>=7"],
        "coverage": ["coverage[toml]"],
    }

    # Using resolve_all
    result_all = resolve_all(groups)

    # Using individual resolve calls
    result_individual = {group: resolve(groups, group) for group in groups}

    assert set(result_all.keys()) == set(result_individual.keys())
    for group in groups:
        assert set(result_all[group]) == set(result_individual[group])
