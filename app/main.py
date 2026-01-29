# app/main.py
from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.database import engine, get_db  # get_db = yield SessionLocal()
from app.db.models import Base, Brew


# ✅ crea tabelle (dev/prototipo). In produzione useresti migrazioni (Alembic).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hoop API ☕", version="0.1.0")


# -----------------------------
# Pydantic models (request/response)
# -----------------------------
class BrewCreate(BaseModel):
    coffee: str = Field(..., min_length=1, max_length=200)
    dose: float = Field(..., gt=0)
    ratio: float = Field(16.0, ge=10, le=25)
    temperature: int = Field(94, ge=70, le=100)
    grind: str = Field("medium", pattern="^(fine|medium|coarse)$")
    rating: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = Field(None, max_length=500)


class BrewUpdate(BaseModel):
    # campi opzionali per patch/update
    coffee: Optional[str] = Field(None, min_length=1, max_length=200)
    dose: Optional[float] = Field(None, gt=0)
    ratio: Optional[float] = Field(None, ge=10, le=25)
    temperature: Optional[int] = Field(None, ge=70, le=100)
    grind: Optional[str] = Field(None, pattern="^(fine|medium|coarse)$")
    rating: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = Field(None, max_length=500)


class BrewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    coffee: str
    dose: float
    ratio: float
    water: float
    temperature: int
    grind: str
    rating: Optional[int] = None
    notes: Optional[str] = None


# -----------------------------
# Business rule (semplice)
# -----------------------------
def tips_for_brew(b: Brew) -> list[str]:
    tips: list[str] = []
    if b.rating is None:
        return ["Aggiungi un rating (1–10) per ricevere suggerimenti."]

    if b.rating <= 5:
        tips.extend([
            "Sembra sottoestratto o poco bilanciato: prova macinatura più fine.",
            "Alza la temperatura di 1–2°C oppure abbassa leggermente il ratio (es. da 16 a 15).",
        ])
    elif b.rating <= 7:
        tips.extend([
            "Buono ma migliorabile: micro-adjust su ratio (±0.5) o grind (mezzo step).",
        ])
    else:
        tips.extend([
            "Ottimo risultato: replica la ricetta e prova a cambiare solo un parametro alla volta.",
        ])
    return tips


# -----------------------------
# Endpoints
# -----------------------------
@app.get("/")
def health():
    return {"status": "ok", "app": "hoop-api"}


@app.post("/brews", response_model=BrewOut, status_code=201)
def create_brew(payload: BrewCreate, db: Session = Depends(get_db)):
    water = round(payload.dose * payload.ratio, 1)

    b = Brew(
        coffee=payload.coffee.strip(),
        dose=payload.dose,
        ratio=payload.ratio,
        water=water,
        temperature=payload.temperature,
        grind=payload.grind,
        rating=payload.rating,
        notes=payload.notes.strip() if payload.notes else None,
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


@app.get("/brews", response_model=List[BrewOut])
def list_brews(limit: int = 50, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 200))
    rows = db.execute(select(Brew).order_by(Brew.id.desc()).limit(limit)).scalars().all()
    return rows


@app.get("/brews/{brew_id}", response_model=BrewOut)
def get_brew(brew_id: int, db: Session = Depends(get_db)):
    b = db.get(Brew, brew_id)
    if not b:
        raise HTTPException(status_code=404, detail="Brew not found")
    return b


@app.patch("/brews/{brew_id}", response_model=BrewOut)
def update_brew(brew_id: int, payload: BrewUpdate, db: Session = Depends(get_db)):
    b = db.get(Brew, brew_id)
    if not b:
        raise HTTPException(status_code=404, detail="Brew not found")

    data = payload.model_dump(exclude_unset=True)

    # Se dose/ratio cambiano, ricalcolo water
    new_dose = data.get("dose", b.dose)
    new_ratio = data.get("ratio", b.ratio)
    if "dose" in data or "ratio" in data:
        b.water = round(new_dose * new_ratio, 1)

    for k, v in data.items():
        if k == "notes" and isinstance(v, str):
            v = v.strip() or None
        if k == "coffee" and isinstance(v, str):
            v = v.strip()
        setattr(b, k, v)

    db.commit()
    db.refresh(b)
    return b


@app.delete("/brews/{brew_id}", status_code=204)
def delete_brew(brew_id: int, db: Session = Depends(get_db)):
    b = db.get(Brew, brew_id)
    if not b:
        raise HTTPException(status_code=404, detail="Brew not found")
    db.delete(b)
    db.commit()
    return None


@app.get("/brews/{brew_id}/tips")
def brew_tips(brew_id: int, db: Session = Depends(get_db)):
    b = db.get(Brew, brew_id)
    if not b:
        raise HTTPException(status_code=404, detail="Brew not found")
    return {"brew_id": brew_id, "tips": tips_for_brew(b)}
