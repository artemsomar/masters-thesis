from pathlib import Path

import pytest

from app.modules.evaluation.dataset_reader import EvaluationDatasetReader
from app.modules.evaluation.errors import InvalidEvaluationDataset


@pytest.mark.unit
def test_dataset_reader_rejects_an_invalid_case_diagram(tmp_path: Path) -> None:
    dataset_path = tmp_path / "dataset"
    case_path = dataset_path / "case"
    case_path.mkdir(parents=True)
    (case_path / "description.txt").write_text("A system description.", encoding="utf-8")
    (case_path / "diagram.json").write_text("not-json", encoding="utf-8")

    with pytest.raises(InvalidEvaluationDataset):
        list(EvaluationDatasetReader().read(dataset_path))
