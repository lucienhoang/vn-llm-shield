from experiments.validate_prompts import validate


def test_prompts_eval_is_valid():
    errors, rows = validate()
    assert errors == []
    assert len(rows) > 0
