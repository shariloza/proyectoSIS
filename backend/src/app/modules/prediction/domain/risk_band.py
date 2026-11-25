from enum import StrEnum
from typing import Final

DISCLAIMER: Final = (
    "Este resultado es una estimación estadística con fines académicos y NO es un "
    "diagnóstico. Si sientes malestar emocional, busca apoyo de un profesional de la "
    "salud mental o de los servicios de bienestar de tu universidad."
)


class RiskBand(StrEnum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


MODERATE_FROM: Final = 0.40
HIGH_FROM: Final = 0.70


def band_for(probability: float) -> RiskBand:
    if not 0 <= probability <= 1:
        raise ValueError(f"probabilidad fuera de [0, 1]: {probability}")
    if probability >= HIGH_FROM:
        return RiskBand.HIGH
    if probability >= MODERATE_FROM:
        return RiskBand.MODERATE
    return RiskBand.LOW
