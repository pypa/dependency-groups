import unittest.mock

import pytest
from packaging.requirements import Requirement

from dependency_groups import DependencyGroupInclude, DependencyGroupResolver


def test_resolver_init_handles_bad_type():
    with pytest.raises(TypeError):
        DependencyGroupResolver([])


def test_resolver_init_catches_normalization_conflict():
    groups = {"test": ["pytest"], "Test": ["pytest", "coverage"]}
    with pytest.raises(ValueError, match="Duplicate dependency group names"):
        DependencyGroupResolver(groups)


def test_lookup_catches_bad_type():
    groups = {"test": ["pytest"]}
    resolver = DependencyGroupResolver(groups)
    with pytest.raises(TypeError):
        resolver.lookup(0)


def test_lookup_on_trivial_normalization():
    groups = {"test": ["pytest"]}
    resolver = DependencyGroupResolver(groups)
    parsed_group = resolver.lookup("Test")
    assert len(parsed_group) == 1
    assert isinstance(parsed_group[0], Requirement)
    req = parsed_group[0]
    assert req.name == "pytest"


def test_lookup_with_include_result():
    groups = {
        "test": ["pytest", {"include-group": "runtime"}],
        "runtime": ["click"],
    }
    resolver = DependencyGroupResolver(groups)
    parsed_group = resolver.lookup("test")
    assert len(parsed_group) == 2

    assert isinstance(parsed_group[0], Requirement)
    assert parsed_group[0].name == "pytest"

    assert isinstance(parsed_group[1], DependencyGroupInclude)
    assert parsed_group[1].include_group == "runtime"


def test_lookup_does_not_trigger_cyclic_include():
    groups = {
        "group1": [{"include-group": "group2"}],
        "group2": [{"include-group": "group1"}],
    }
    resolver = DependencyGroupResolver(groups)
    parsed_group = resolver.lookup("group1")
    assert len(parsed_group) == 1

    assert isinstance(parsed_group[0], DependencyGroupInclude)
    assert parsed_group[0].include_group == "group2"


def test_expand_contract_model_only_does_inner_lookup_once():
    groups = {
        "root": [
            {"include-group": "mid1"},
            {"include-group": "mid2"},
            {"include-group": "mid3"},
            {"include-group": "mid4"},
        ],
        "mid1": [{"include-group": "contract"}],
        "mid2": [{"include-group": "contract"}],
        "mid3": [{"include-group": "contract"}],
        "mid4": [{"include-group": "contract"}],
        "contract": [{"include-group": "leaf"}],
        "leaf": ["attrs"],
    }
    resolver = DependencyGroupResolver(groups)

    real_inner_resolve = resolver._resolve
    with unittest.mock.patch(
        "dependency_groups.DependencyGroupResolver._resolve",
        side_effect=real_inner_resolve,
    ) as spy:
        resolved = resolver.resolve("root")
        assert len(resolved) == 4
        assert all(item.name == "attrs" for item in resolved)

        # each of the `mid` nodes will call resolution with `contract`, but only the
        # first of those evaluations should call for resolution of `leaf` -- after that,
        # `contract` will be in the cache and `leaf` will not need to be resolved
        spy.assert_any_call("leaf", "root")
        leaf_calls = [c for c in spy.mock_calls if c.args[0] == "leaf"]
        assert len(leaf_calls) == 1


def test_no_double_parse():
    groups = {
        "test": [{"include-group": "runtime"}],
        "runtime": ["click"],
    }
    resolver = DependencyGroupResolver(groups)

    parse = resolver.lookup("test")
    assert len(parse) == 1
    assert isinstance(parse[0], DependencyGroupInclude)
    assert parse[0].include_group == "runtime"

    mock_include = DependencyGroupInclude(include_group="perfidy")

    with unittest.mock.patch(
        "dependency_groups._implementation.DependencyGroupInclude",
        return_value=mock_include,
    ):
        # rerunning with that resolver will not re-resolve
        reparse = resolver.lookup("test")
        assert len(reparse) == 1
        assert isinstance(reparse[0], DependencyGroupInclude)
        assert reparse[0].include_group == "runtime"

        # but verify that a fresh resolver (no cache) will get the mock
        deceived_resolver = DependencyGroupResolver(groups)
        deceived_parse = deceived_resolver.lookup("test")
        assert len(deceived_parse) == 1
        assert isinstance(deceived_parse[0], DependencyGroupInclude)
        assert deceived_parse[0].include_group == "perfidy"


@pytest.mark.parametrize("group_name_declared", ("foo-bar", "foo_bar", "foo..bar"))
@pytest.mark.parametrize("group_name_used", ("foo-bar", "foo_bar", "foo..bar"))
def test_normalized_name_is_used_for_include_group_lookups(
    group_name_declared, group_name_used
):
    groups = {
        group_name_declared: ["spam"],
        "eggs": [{"include-group": group_name_used}],
    }
    resolver = DependencyGroupResolver(groups)

    result = resolver.resolve("eggs")
    assert len(result) == 1
    assert isinstance(result[0], Requirement)
    req = result[0]
    assert req.name == "spam"
