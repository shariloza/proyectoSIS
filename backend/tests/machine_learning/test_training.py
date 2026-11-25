from app.machine_learning.dataset import PreparedDataset
from app.machine_learning.evaluation import ACCEPTANCE_CRITERIA, check_acceptance, no_regression
from app.machine_learning.training import Candidate, split_dataset, train


def test_split_is_stratified_and_disjoint(prepared: PreparedDataset) -> None:
    split = split_dataset(prepared.features, prepared.target)

    indexes = [
        set(part.index)
        for part in (split.train_features, split.validation_features, split.test_features)
    ]
    assert not (indexes[0] & indexes[1] or indexes[0] & indexes[2] or indexes[1] & indexes[2])
    assert sum(map(len, indexes)) == len(prepared.features)
    overall = prepared.target.mean()
    for target in (split.train_target, split.validation_target, split.test_target):
        assert abs(target.mean() - overall) < 0.02


def test_training_is_reproducible_with_fixed_seed(
    prepared: PreparedDataset, fast_candidates: list[Candidate]
) -> None:
    first = train(prepared.features, prepared.target, fast_candidates)
    second = train(prepared.features, prepared.target, fast_candidates)

    assert first.test_metrics == second.test_metrics
    assert first.comparison == second.comparison


def test_dummy_is_never_selected(
    prepared: PreparedDataset, fast_candidates: list[Candidate]
) -> None:
    result = train(prepared.features, prepared.target, fast_candidates)

    assert result.algorithm == "LogisticRegression"
    assert result.comparison[0]["algorithm"] == "DummyClassifier"
    assert result.test_metrics["roc_auc"] > result.comparison[0]["validation_roc_auc"]


def test_acceptance_reports_every_criterion_and_fails_if_any_fails() -> None:
    metrics = {
        "roc_auc": 0.90,
        "f1_macro": 0.80,
        "per_class": {"1": {"recall": 0.70, "precision": 0.80}},
        "recall_by_gender": {"Male": 0.70, "Female": 0.71},
    }

    report = check_acceptance(
        metrics, validation_roc_auc=0.89, baseline_roc_auc=0.5, latency_milliseconds=5
    )

    assert len(report["criteria"]) == len(ACCEPTANCE_CRITERIA)
    failed = [c["code"] for c in report["criteria"] if not c["passed"]]
    assert failed == ["C2"]
    assert report["approved"] is False


def test_retraining_cannot_degrade_active_model() -> None:
    assert no_regression(candidate_roc_auc=0.865, active_roc_auc=0.870)
    assert not no_regression(candidate_roc_auc=0.850, active_roc_auc=0.870)
