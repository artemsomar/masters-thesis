import pytest

from app.modules.evaluation.hungarian import maximum_weight_assignment


@pytest.mark.unit
def test_hungarian_finds_the_global_maximum_weight_matching() -> None:
    assignment = maximum_weight_assignment([[0.9, 0.8], [0.85, 0.1]])

    assert set(assignment) == {(0, 1), (1, 0)}
    assert set(maximum_weight_assignment([[0.1, 0.9], [0.8, 0.2], [0.7, 0.6]])) == {
        (0, 1),
        (1, 0),
    }
