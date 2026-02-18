# app/services/brew_service.py
from __future__ import annotations

from typing import Optional


def tips_for_brew(rating: Optional[int]) -> list[str]:
    """
    Genera suggerimenti basati sul rating per migliorare la brew.

    Args:
        rating: Valutazione 1-10 della brew (None se non ancora valutata).

    Returns:
        Lista di suggerimenti basati sul rating.
    """
    if rating is None:
        return ["Aggiungi un rating (1–10) per ricevere suggerimenti."]

    if rating <= 5:
        return [
            "Sembra sottoestratto o sbilanciato: prova macinatura più fine.",
            "Alza la temperatura di 1–2°C oppure abbassa leggermente il ratio (es. da 16 a 15).",
        ]
    if rating <= 7:
        return ["Buono ma migliorabile: micro-adjust su ratio (±0.5) o grind (mezzo step)."]
    return ["Ottimo risultato: replica la ricetta e prova a cambiare solo un parametro alla volta."]


def calculate_water(dose: float, ratio: float) -> float:
    """
    Calcola la quantità d'acqua in base a dose e ratio.

    Args:
        dose: Dose di caffè in grammi.
        ratio: Rapporto acqua/caffè.

    Returns:
        Quantità d'acqua in grammi, arrotondata a 1 decimale.
    """
    return round(dose * ratio, 1)
