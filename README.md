# Hoop API

API REST per la registrazione e il tracciamento delle estrazioni di caffè con la macchina **Ceado Hoop**.

Costruita con **FastAPI** e **PostgreSQL**, permette di salvare ogni estrazione con i suoi parametri (dose, ratio, temperatura, macinatura) e ricevere suggerimenti automatici per migliorarla in base al rating.

---

## Stack

Python 3.12 / FastAPI
PostgreSQL + psycopg
Docker Compose

## Schemi Pydantic

Ogni estrazione transita attraverso schemi Pydantic che separano chiaramente input, aggiornamento e output:

- `BrewCreate` — input del client (senza `water`, lo calcola il server)
- `BrewUpdate` — tutti i campi opzionali per il PATCH
- `BrewOut` — risposta completa, include `id`, `water`, `created_at`
- `BrewCreated` — risposta del POST, restituisce solo l'`id`
- `TipsOut` — risposta di `/tips`, contiene la lista di suggerimenti

---

## Struttura del progetto

```
hoop_app/
├── app/
│   ├── main.py
│   ├── domain/schemas.py
│   ├── services/brew_service.py
│   └── db/
│       ├── database.py
│       └── init_db.py
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_brew_service.py
├── docker-compose.yml
├── requirements.txt
└── requirements-dev.txt
```

---

## Avvio in locale

```bash
git clone https://github.com/MarcoCasciano/hoop_app.git
cd hoop_app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

docker compose up -d db
uvicorn app.main:app --reload
```

API su `http://localhost:8000`

docs su `http://localhost:8000/docs`

Per avviare tutto con Docker:
```bash
cp .env.docker.example .env.docker
docker compose up
```
---

## Endpoint

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/brews` | Crea una nuova estrazione |
| `GET` | `/brews` | Lista delle ultime estrazioni (default 50, max 200) |
| `GET` | `/brews/{id}` | Dettaglio di una singola estrazione |
| `PATCH` | `/brews/{id}` | Aggiornamento parziale di un'estrazione |
| `DELETE` | `/brews/{id}` | Eliminazione di un'estrazione |
| `GET` | `/brews/{id}/tips` | Suggerimenti per migliorare l'estrazione |

### Esempio: crea una brew

```bash
curl -X POST http://localhost:8000/brews \
  -H "Content-Type: application/json" \
  -d '{
    "coffee": "Ethiopia Yirgacheffe",
    "dose": 18.0,
    "ratio": 16.0,
    "temperature": 94,
    "grind": "medium",
    "rating": 7,
    "notes": "floreale, acidità intensa"
  }'
```

Il campo `water` viene calcolato automaticamente dal server (`dose × ratio`).

---

## Test

### Requisiti

Avvia il database di test (se non è già in esecuzione):

```bash
docker compose up -d db
docker exec hoop_db psql -U hoop -d hoop_db -c "CREATE DATABASE hoop_test_db;"
```

Installa le dipendenze di sviluppo:

```bash
pip install -r requirements-dev.txt
```

### Esegui i test

```bash
pytest tests/ -v
```

I test unitari (service layer) non richiedono il database e girano anche senza Docker:

```bash
pytest tests/test_brew_service.py -v
```
