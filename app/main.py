# app/main.py
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from psycopg import Connection

from app.db.database import get_conn
from app.db.init_db import init_db
from app.domain.schemas import BrewCreate, BrewUpdate, BrewCreated, BrewOut, TipsOut, HealthOut
from app.services.brew_service import tips_for_brew, calculate_water


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inizializza il database all'avvio dell'app."""
    init_db()
    yield


app = FastAPI(
    title="Hoop API",
    version="0.1.0",
    description="API per la gestione delle estrazioni di caffè con Ceado Hoop",
    lifespan=lifespan,
)


# --- Endpoints ---

@app.get("/", response_model=HealthOut, tags=["System"])
def health():
    """Health check: verifica che il servizio sia attivo."""
    return {"status": "ok", "app": "hoop-api"}


@app.post("/brews", response_model=BrewCreated, status_code=201, tags=["Brews"])
def create_brew(payload: BrewCreate, conn: Connection = Depends(get_conn)):
    """
    Crea una nuova registrazione di estrazione.
    L'acqua viene calcolata automaticamente da dose × ratio.
    """
    water = calculate_water(payload.dose, payload.ratio)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO brews (coffee, dose, ratio, water, temperature, grind, rating, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (
                payload.coffee.strip(),
                payload.dose,
                payload.ratio,
                water,
                payload.temperature,
                payload.grind,
                payload.rating,
                payload.notes.strip() if payload.notes else None,
            ),
        )
        new_id = cur.fetchone()["id"]
        conn.commit()

    return {"id": new_id}


@app.get("/brews", response_model=List[BrewOut], tags=["Brews"])
def list_brews(limit: int = 50, conn: Connection = Depends(get_conn)):
    """
    Recupera le ultime estrazioni effettuate.

    Args:
        limit: Numero massimo di risultati (default 50, max 200).
    """
    limit = max(1, min(limit, 200))
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, coffee, dose, ratio, water, temperature, grind, rating, notes, created_at
            FROM brews
            ORDER BY id DESC
            LIMIT %s;
            """,
            (limit,),
        )
        rows = cur.fetchall()
    return rows


@app.get("/brews/{brew_id}", response_model=BrewOut, tags=["Brews"])
def get_brew(brew_id: int, conn: Connection = Depends(get_conn)):
    """Recupera i dettagli di una singola estrazione."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, coffee, dose, ratio, water, temperature, grind, rating, notes, created_at
            FROM brews
            WHERE id = %s;
            """,
            (brew_id,),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Brew not found")
    return row


@app.patch("/brews/{brew_id}", response_model=BrewOut, tags=["Brews"])
def update_brew(brew_id: int, payload: BrewUpdate, conn: Connection = Depends(get_conn)):
    """Aggiorna parzialmente una brew già salvata. Ricalcola l'acqua se dose o ratio cambiano."""
    data = payload.model_dump(exclude_unset=True)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, coffee, dose, ratio, water, temperature, grind, rating, notes, created_at
            FROM brews
            WHERE id = %s;
            """,
            (brew_id,),
        )
        current = cur.fetchone()

        if not current:
            raise HTTPException(status_code=404, detail="Brew not found")

        if "dose" in data or "ratio" in data:
            new_dose = data.get("dose", current["dose"])
            new_ratio = data.get("ratio", current["ratio"])
            data["water"] = calculate_water(float(new_dose), float(new_ratio))

        if "coffee" in data and isinstance(data["coffee"], str):
            data["coffee"] = data["coffee"].strip()

        if "notes" in data and isinstance(data["notes"], str):
            data["notes"] = data["notes"].strip() or None

        if not data:
            return current

        allowed = {"coffee", "dose", "ratio", "water", "temperature", "grind", "rating", "notes"}
        sets = []
        values = []
        for k, v in data.items():
            if k in allowed:
                sets.append(f"{k} = %s")
                values.append(v)

        values.append(brew_id)

        cur.execute(
            f"""
            UPDATE brews
            SET {", ".join(sets)}
            WHERE id = %s
            RETURNING id, coffee, dose, ratio, water, temperature, grind, rating, notes, created_at;
            """,
            tuple(values),
        )
        updated = cur.fetchone()
        conn.commit()

    return updated


@app.delete("/brews/{brew_id}", status_code=204, tags=["Brews"])
def delete_brew(brew_id: int, conn: Connection = Depends(get_conn)):
    """Elimina una brew dal database."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM brews WHERE id = %s RETURNING id;",
            (brew_id,),
        )
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Brew not found")
    return None


@app.get("/brews/{brew_id}/tips", response_model=TipsOut, tags=["Brews"])
def brew_tips(brew_id: int, conn: Connection = Depends(get_conn)):
    """Restituisce suggerimenti personalizzati basati sul rating della brew."""
    with conn.cursor() as cur:
        cur.execute("SELECT rating FROM brews WHERE id = %s;", (brew_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Brew not found")
    return {"brew_id": brew_id, "tips": tips_for_brew(row["rating"])}
