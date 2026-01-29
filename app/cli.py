# Command Line Interface
# Interfaccia utente che si avvale di comandi di testo del terminale

from __future__ import annotations

import typer
from sqlalchemy import select

from app.db.database import SessionLocal, engine
from app.db.models import Base, Brew

app = typer.Typer(help="Hoop Coffee CLI ☕")

# Assicura che DB e tabelle esistano anche se non hai avviato FastAPI
Base.metadata.create_all(bind=engine)


@app.command()
def brew(
    coffee: str = typer.Option(..., help="Nome del caffè / roaster"),
    dose: float = typer.Option(..., help="Dose in grammi, es. 18"),
    ratio: float = typer.Option(16.0, help="Ratio acqua, es. 16.0 per 1:16"),
    temp: int = typer.Option(94, help="Temperatura in °C"),
    grind: str = typer.Option("medium", help="fine | medium | coarse (testuale)"),
    rating: int | None = typer.Option(None, help="Voto 1-10 (opzionale)"),
    notes: str | None = typer.Option(None, help="Note (opzionale)"),
):
    """Salva un brew nel database."""
    water = round(dose * ratio, 1)

    db = SessionLocal()
    try:
        b = Brew(
            coffee=coffee,
            dose=dose,
            ratio=ratio,
            water=water,
            temperature=temp,
            grind=grind,
            rating=rating,
            notes=notes,
        )
        db.add(b)
        db.commit()
        db.refresh(b)
    finally:
        db.close()

    typer.echo(f"✅ Salvato brew #{b.id}")
    typer.echo(f"☕ {coffee} | {dose}g | {water}ml | {temp}°C | grind={grind} | rating={rating}")


@app.command()
def history(limit: int = typer.Option(20, help="Numero massimo di brew da mostrare")):
    """Mostra gli ultimi brew salvati."""
    db = SessionLocal()
    try:
        rows = db.execute(select(Brew).order_by(Brew.id.desc()).limit(limit)).scalars().all()
    finally:
        db.close()

    if not rows:
        typer.echo("Nessun brew salvato ancora. Prova: python -m app.cli brew --coffee Test --dose 18")
        raise typer.Exit(code=0)

    for b in rows:
        typer.echo(
            f"[{b.id}] {b.coffee} | dose={b.dose}g | water={b.water}ml | temp={b.temperature}°C | "
            f"grind={b.grind} | rating={b.rating}"
        )


@app.command()
def show(brew_id: int):
    """Mostra i dettagli di un brew."""
    db = SessionLocal()
    try:
        b = db.get(Brew, brew_id)
    finally:
        db.close()

    if not b:
        typer.echo("❌ Brew non trovato")
        raise typer.Exit(code=1)

    typer.echo(f"#{b.id} — {b.coffee}")
    typer.echo(f"Dose: {b.dose} g")
    typer.echo(f"Ratio: 1:{b.ratio}")
    typer.echo(f"Acqua: {b.water} ml")
    typer.echo(f"Temp: {b.temperature} °C")
    typer.echo(f"Grind: {b.grind}")
    typer.echo(f"Rating: {b.rating}")
    typer.echo(f"Notes: {b.notes}")


if __name__ == "__main__":
    app()
