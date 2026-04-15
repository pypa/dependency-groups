import pytest

from dependency_groups import resolve, resolve_all


def test_empty_group():
    groups = {"test": []}
    assert resolve(groups, "test") == ()


def test_str_list_group():
    groups = {"test": ["pytest"]}
    assert resolve(groups, "test") == ("pytest",)


def test_single_include_group():
    groups = {
        "test": [
            "pytest",
            {"include-group": "runtime"},
        ],
        "runtime": ["sqlalchemy"],
    }
    assert set(resolve(groups, "test")) == {"pytest", "sqlalchemy"}


def test_sdual_include_group():
    groups = {
        "test": [
            "pytest",
        ],
        "runtime": ["sqlalchemy"],
    }
    assert set(resolve(groups, "test", "runtime")) == {"pytest", "sqlalchemy"}


def test_normalized_group_name():
    groups = {
        "TEST": ["pytest"],
    }
    assert resolve(groups, "test") == ("pytest",)


def test_malformed_group_data():
    groups = [{"test": ["pytest"]}]
    with pytest.raises(TypeError, match="Dependency Groups table is not a mapping"):
        resolve(groups, "test")


def test_malformed_group_query():
    groups = {"test": ["pytest"]}
    with pytest.raises(TypeError, match="Dependency group name is not a str"):
        resolve(groups, 0)


def test_no_such_group_name():
    groups = {
        "test": ["pytest"],
    }
    with pytest.raises(LookupError, match="'testing' not found"):
        resolve(groups, "testing")


def test_duplicate_normalized_name():
    groups = {
        "test": ["pytest"],
        "TEST": ["nose2"],
    }
    with pytest.raises(
        ValueError,
        match=r"Duplicate dependency group names: test \((test, TEST)|(TEST, test)\)",
    ):
        resolve(groups, "test")


def test_cyclic_include():
    groups = {
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


def test_cyclic_include_many_steps():
    groups = {}
    for i in range(100):
        groups[f"group{i}"] = [{"include-group": f"group{i + 1}"}]
    groups["group100"] = [{"include-group": "group0"}]
    with pytest.raises(
        ValueError,
        match="Cyclic dependency group include while resolving group0:",
    ):
        resolve(groups, "group0")


def test_cyclic_include_self():
    groups = {
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


def test_cyclic_include_ring_under_root():
    groups = {
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


def test_non_list_data():
    groups = {"test": "pytest, coverage"}
    with pytest.raises(TypeError, match="Dependency group 'test' is not a list"):
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
def test_unknown_object_shape(item):
    groups = {"test": [item]}
    with pytest.raises(ValueError, match="Invalid dependency group item:"):
        resolve(groups, "test")


def test_resolve_all_empty():
    groups = {}
    assert resolve_all(groups) == {}


def test_resolve_all_single_group():
    groups = {"test": ["pytest"]}
    assert resolve_all(groups) == {"test": ("pytest",)}


def test_resolve_all_multiple_groups():
    groups = {
        "test": ["pytest", {"include-group": "runtime"}],
        "runtime": ["sqlalchemy"],
    }
    result = resolve_all(groups)
    assert "test" in result
    assert "runtime" in result
    assert set(result["test"]) == {"pytest", "sqlalchemy"}
    assert result["runtime"] == ("sqlalchemy",)


def test_resolve_all_with_normalize_false():
    groups = {
        "TEST": ["pytest"],
    }
    result = resolve_all(groups, normalize=False)
    assert "TEST" in result
    assert result["TEST"] == ("pytest",)


def test_resolve_all_with_normalize_true():
    groups = {
        "TEST": ["pytest"],
    }
    result = resolve_all(groups, normalize=True)
    assert "test" in result
    assert result["test"] == ("pytest",)


def test_resolve_all_default_preserves_names():
    """Test that normalize=False is the default."""
    groups = {
        "TEST": ["pytest"],
    }
    result = resolve_all(groups)
    assert "TEST" in result
    assert "test" not in result
    assert result["TEST"] == ("pytest",)


def test_resolve_all_shared_includes():
    """Test that resolve_all correctly handles groups with shared includes.

    Structure:
        dev = [{include-group = "test"}, {include-group = "lint"}]
        test = [{include-group = "pytest"}, {include-group = "coverage"}]
        lint = ["prek", {include-group = "typing"}]
        typing = ["mypy"]
        pytest = ["pytest>=7"]
        coverage = ["coverage[toml]"]
    """
    groups = {
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


def test_resolve_all_uses_cache():
    """Test that resolve_all uses the resolver's internal cache properly.

    This tests that calling resolve_all uses the optimized resolve_all method
    which avoids duplicate work when groups share includes.
    """
    from dependency_groups._implementation import DependencyGroupResolver

    groups = {
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


def test_resolve_all_vs_individual_resolve():
    """Test that resolve_all produces the same results as individual resolve calls."""
    groups = {
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
