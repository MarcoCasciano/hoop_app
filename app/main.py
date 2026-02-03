# app/main.py  (NO SQLALCHEMY)
from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field

from psycopg import Connection

from app.db.database import get_conn
from app.db.init_db import init_db

app = FastAPI(title="Hoop API", version="0.1.0")

# inizializzazione db
@app.on_event("startup")
def on_startup():
    init_db()

# modelli Pydantic input/output

# modello pydantic di input
# descrive struttura json quando creo una brew
class BrewCreate(BaseModel):
    coffee: str = Field(..., min_length=1, max_length=200)
    dose: float = Field(..., gt=0)
    ratio: float = Field(16.0, ge=10, le=25)
    temperature: int = Field(94, ge=70, le=100)
    grind: str = Field("medium", pattern="^(fine|medium|coarse)$")
    rating: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = Field(None, max_length=500)

# gestisce eventuale modifica di brew già salvata nel database
class BrewUpdate(BaseModel):
    coffee: Optional[str] = Field(None, min_length=1, max_length=200)
    dose: Optional[float] = Field(None, gt=0)
    ratio: Optional[float] = Field(None, ge=10, le=25)
    temperature: Optional[int] = Field(None, ge=70, le=100)
    grind: Optional[str] = Field(None, pattern="^(fine|medium|coarse)$")
    rating: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = Field(None, max_length=500)

# modello pydantic di output
# quello che il client riceva dopo la get al db
class BrewOut(BaseModel):
    id: int # identificatore per leggere nel db
    coffee: str
    dose: float
    ratio: float
    water: float # include valore water calcolato autonomamente
    temperature: int
    grind: str
    rating: Optional[int] = None
    notes: Optional[str] = None

# semplice business rule

def tips_for_brew(rating: Optional[int]) -> list[str]:
    """
        Genera suggerimenti per migliorare la brew

        Args:
            rating: Valutazione 1-10 della brew (ritorna None se non valutata)

        Returns:
            Lista di suggerimenti basati sul rating:
            - 1-5: sottoestratto → macinatura più fine, temperatura più alta
            - 6-7: buono → micro-aggiustamenti
            - 8-10: ottimo → replica e sperimenta con cautela
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


# Endpoints

# --- health check --- verifica app attiva e in funzione
@app.get("/")
def health():
    return {"status": "ok", "app": "hoop-api"}

# --- POST /brews --- crea una nuova brew nel db

# FastAPI e Pydantic leggono il body della richiesta, validano JSON contro
# modello BrewCreate, creano istanza BrewCreate e la passano come parametro payload alla funzione
@app.post("/brews", response_model=dict, status_code=201)
def create_brew(payload: BrewCreate, conn: Connection = Depends(get_conn)):
    water = round(payload.dose * payload.ratio, 1)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO brews (coffee, dose, ratio, water, temperature, grind, rating, notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
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
        new_id = cur.fetchone()["id"] # recupero una riga alla volta con fetchone
        conn.commit()

    return {"id": new_id}

# --- GET /brews --- restituisce lista delle brews dalla più recente

# dopo execute la query viene inviata a PostgreSQL che la esegue quindi
# i risultati sono pronti sul server ma non ancora in Python
# fetchall recupera ogni riga e la trasforma in un oggetto Python
@app.get("/brews", response_model=List[BrewOut])
def list_brews(limit: int = 50, conn: Connection = Depends(get_conn)):
    limit = max(1, min(limit, 200)) # min = 1, max = 200
    with conn.cursor() as cur:
        # query SQL
        cur.execute(
            """
            SELECT id, coffee, dose, ratio, water, temperature, grind, rating, notes
            FROM brews
            ORDER BY id DESC
            LIMIT %s;
            """,
            (limit,),
        )
        rows = cur.fetchall() # scarica tutte le righe dalla query in una lista Python
    return rows  # dict_row, compatibile con Pydantic

# --- GET /brews/{brew_id} --- recupera singola brew
@app.get("/brews/{brew_id}", response_model=BrewOut)
def get_brew(brew_id: int, conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        # query SQL
        cur.execute(
            """
            SELECT id, coffee, dose, ratio, water, temperature, grind, rating, notes
            FROM brews
            WHERE id = %s;
            """,
            (brew_id,),
        )
        row = cur.fetchone()
    if not row: # se la riga non esiste
        raise HTTPException(status_code=404, detail="Brew not found")
    return row

# --- PATCH /brews/{brew_id} --- aggiorna una brew già salvata nel db
@app.patch("/brews/{brew_id}", response_model=BrewOut)
def update_brew(brew_id: int, payload: BrewUpdate, conn: Connection = Depends(get_conn)):
    # estrazione campi inviati
    data = payload.model_dump(exclude_unset=True) # estrai solo i campi presenti nel JSON

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, coffee, dose, ratio, water, temperature, grind, rating, notes
            FROM brews
            WHERE id = %s;
            """,
            (brew_id,),
        )
        # verifica esistenza campi
        current = cur.fetchone()

        if not current:
            raise HTTPException(status_code=404, detail="Brew not found")

        # se si cambia dose o ratio l'acqua viene ricalcolata
        new_dose = data.get("dose", current["dose"])
        new_ratio = data.get("ratio", current["ratio"])
        if "dose" in data or "ratio" in data:
            data["water"] = round(float(new_dose) * float(new_ratio), 1)

        if "coffee" in data and isinstance(data["coffee"], str):
            data["coffee"] = data["coffee"].strip()

        if "notes" in data and isinstance(data["notes"], str):
            data["notes"] = data["notes"].strip() or None

        # se non ci sono campi ritorna stato corrente
        if not data:
            return current

        # query dinamica
        # meto controllo altrimenti si potrebbero per es assumere privilegi di amministratore
        allowed = {"coffee","dose","ratio","water","temperature","grind","rating","notes"}
        sets = [] # clausole set
        values = [] # valori da sostituire ai placeholder %s
        for k, v in data.items(): # filtro, accetta solo campi autorizzati
            if k in allowed:
                sets.append(f"{k} = %s")
                values.append(v)

        values.append(brew_id)

        # update SQL, query con f-string
        cur.execute(
            f"""
            UPDATE brews
            SET {", ".join(sets)}
            WHERE id = %s
            RETURNING id, coffee, dose, ratio, water, temperature, grind, rating, notes;
            """,
            tuple(values), # psycopg richiede una tupla o una sequenza immutabile
        )
        updated = cur.fetchone()
        conn.commit()

    return updated

# --- DELETE /brews/{brew_id} --- elimina una brew dal db
@app.delete("/brews/{brew_id}", status_code=204)
def delete_brew(brew_id: int, conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        # query SQL
        cur.execute("""
            DELETE FROM brews 
            WHERE id = %s 
            RETURNING id;
        """,
        (brew_id,)
        )
        row = cur.fetchone()
        conn.commit()
    if not row: # se la riga non esiste
        raise HTTPException(status_code=404, detail="Brew not found")
    return None

# --- GET /brews/{brew_id}/tips --- suggerimenti
# restituisce suggerimenti personalizzati basati sul rating immesso
@app.get("/brews/{brew_id}/tips")
def brew_tips(brew_id: int, conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        # query SQL - recupera solo il rating
        cur.execute("""
            SELECT rating FROM brews 
            WHERE id = %s;
        """,
        (brew_id,)
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Brew not found")
    return {"brew_id": brew_id, "tips": tips_for_brew(row["rating"])}
