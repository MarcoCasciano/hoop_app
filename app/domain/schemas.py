# app/domain/schemas.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BrewCreate(BaseModel):
    """
    Schema di validazione dell'input per la creazione di una nuova estrazione.
    Descrive la struttura del JSON con tutti i parametri necessari per definire la brew.
    """
    coffee: str = Field(..., min_length=1, max_length=200)
    dose: float = Field(..., gt=0)
    ratio: float = Field(16.0, ge=10, le=25)
    temperature: int = Field(94, ge=70, le=100)
    grind: str = Field("medium", pattern="^(fine|medium|coarse)$")
    rating: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = Field(None, max_length=500)


class BrewUpdate(BaseModel):
    """
    Schema per l'aggiornamento parziale di una brew già salvata.
    Tutti i campi sono opzionali.
    """
    coffee: Optional[str] = Field(None, min_length=1, max_length=200)
    dose: Optional[float] = Field(None, gt=0)
    ratio: Optional[float] = Field(None, ge=10, le=25)
    temperature: Optional[int] = Field(None, ge=70, le=100)
    grind: Optional[str] = Field(None, pattern="^(fine|medium|coarse)$")
    rating: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = Field(None, max_length=500)


class BrewCreated(BaseModel):
    """Schema di risposta per la creazione di una brew. Restituisce solo l'id assegnato."""
    id: int


class BrewOut(BaseModel):
    """
    Schema di output per una brew.
    Include tutti i parametri dell'estrazione, l'acqua calcolata dal server e la data di creazione.
    """
    id: int
    coffee: str
    dose: float
    ratio: float
    water: float
    temperature: int
    grind: str
    rating: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime


class TipsOut(BaseModel):
    """Schema di risposta per i suggerimenti di una brew."""
    brew_id: int
    tips: list[str]


class HealthOut(BaseModel):
    """Schema di risposta per l'health check."""
    status: str
    app: str
