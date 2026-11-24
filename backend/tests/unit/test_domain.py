import uuid

import pytest

from app.modules.auth.infrastructure.security import (
    InvalidTokenError,
    PasswordHasher,
    TokenService,
)
from app.modules.model_registry.domain.status import ModelStatus, ensure_can_activate
from app.modules.prediction.domain.risk_band import RiskBand, band_for
from app.shared.errors import ConflictError, RateLimitedError
from app.shared.rate_limit import RateLimiter


@pytest.mark.parametrize(
    ("probability", "band"),
    [
        (0.0, RiskBand.LOW),
        (0.399, RiskBand.LOW),
        (0.40, RiskBand.MODERATE),
        (0.699, RiskBand.MODERATE),
        (0.70, RiskBand.HIGH),
        (1.0, RiskBand.HIGH),
    ],
)
def test_risk_band_boundaries(probability: float, band: RiskBand) -> None:
    assert band_for(probability) == band


def test_risk_band_rejects_invalid_probability() -> None:
    with pytest.raises(ValueError, match="fuera de"):
        band_for(1.2)


@pytest.mark.parametrize("status", [ModelStatus.APPROVED, ModelStatus.RETIRED])
def test_approved_or_retired_models_can_be_activated(status: ModelStatus) -> None:
    ensure_can_activate(status)


@pytest.mark.parametrize(
    "status", [ModelStatus.CANDIDATE, ModelStatus.REJECTED, ModelStatus.ACTIVE]
)
def test_other_states_cannot_be_activated(status: ModelStatus) -> None:
    with pytest.raises(ConflictError):
        ensure_can_activate(status)


def test_rate_limiter_blocks_after_limit_per_key() -> None:
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    limiter.check("a")
    limiter.check("a")

    with pytest.raises(RateLimitedError):
        limiter.check("a")
    limiter.check("b")


def test_password_hash_roundtrip() -> None:
    hasher = PasswordHasher()
    hashed = hasher.hash("correct horse")

    assert hasher.verify(hashed, "correct horse")
    assert not hasher.verify(hashed, "wrong")
    assert not hasher.verify("not-a-hash", "correct horse")


def _tokens(**overrides: object) -> TokenService:
    params: dict[str, object] = {
        "secret": "s" * 32,
        "issuer": "iss",
        "audience": "aud",
        "expire_minutes": 5,
    }
    return TokenService(**(params | overrides))  # type: ignore[arg-type]


def test_token_roundtrip() -> None:
    subject = uuid.uuid4()
    claims = _tokens().verify(_tokens().issue(subject, "admin"))

    assert claims["sub"] == str(subject)
    assert claims["role"] == "admin"


@pytest.mark.parametrize(
    "verifier",
    [
        {"secret": "x" * 32},
        {"issuer": "other-issuer"},
        {"audience": "other-audience"},
    ],
)
def test_token_rejects_wrong_signature_issuer_or_audience(verifier: dict[str, object]) -> None:
    token = _tokens().issue(uuid.uuid4(), "admin")

    with pytest.raises(InvalidTokenError):
        _tokens(**verifier).verify(token)


def test_token_rejects_expired() -> None:
    token = _tokens(expire_minutes=-1).issue(uuid.uuid4(), "admin")

    with pytest.raises(InvalidTokenError, match="expired"):
        _tokens().verify(token)
