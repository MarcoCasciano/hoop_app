from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from sqlalchemy import select

from app.db.database import SessionLocal, engine
from app.db.models import Base, Brew


class HoopGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        # DEBUG: assicura che stai eseguendo davvero questo file
        print(">>> STO ESEGUENDO app/gui.py:", __file__)

        self.title("Hoop Companion ☕")
        self.geometry("940x540")
        self.minsize(880, 500)

        # assicura che DB e tabelle esistano
        Base.metadata.create_all(bind=engine)

        self._build_ui()
        self._load_history()

        # focus iniziale sul campo coffee
        self.after(150, lambda: self.entry_coffee.focus_set())

    # ---------- UI ----------
    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=10)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Hoop Companion", font=("Helvetica", 18, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text="GUI Tkinter OOP — salva brew su SQLite e visualizza lo storico.",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        body = ttk.Frame(self, padding=10)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # left: form
        self.form = ttk.LabelFrame(body, text="Nuova brew", padding=10)
        self.form.grid(row=0, column=0, sticky="ns", padx=(0, 10))

        # right: history table
        self.history_box = ttk.LabelFrame(body, text="Storico (DB)", padding=10)
        self.history_box.grid(row=0, column=1, sticky="nsew")
        self.history_box.columnconfigure(0, weight=1)
        self.history_box.rowconfigure(0, weight=1)

        self._build_form(self.form)
        self._build_table(self.history_box)

    def _build_form(self, parent: ttk.Frame) -> None:
        # Variabili per campi numerici/testo (coffee lo leggiamo DIRETTAMENTE dall'Entry)
        self.var_dose = tk.StringVar(value="16")
        self.var_ratio = tk.StringVar(value="16")
        self.var_temp = tk.StringVar(value="94")
        self.var_grind = tk.StringVar(value="medium")
        self.var_rating = tk.StringVar(value="")
        self.var_notes = tk.StringVar(value="")
        self.var_water_preview = tk.StringVar(value="Acqua: - ml")

        r = 0

        # COFFEE (fix definitivo): niente StringVar, leggiamo dall'Entry con .get()
        ttk.Label(parent, text="Coffee *").grid(row=r, column=0, sticky="w")
        self.entry_coffee = ttk.Entry(parent, width=28)
        self.entry_coffee.grid(row=r, column=1, sticky="ew", pady=4)
        r += 1

        ttk.Label(parent, text="Dose (g) *").grid(row=r, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.var_dose, width=12).grid(row=r, column=1, sticky="w", pady=4)
        r += 1

        ttk.Label(parent, text="Ratio (es. 16 = 1:16)").grid(row=r, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.var_ratio, width=12).grid(row=r, column=1, sticky="w", pady=4)
        r += 1

        ttk.Label(parent, text="Temp (°C)").grid(row=r, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.var_temp, width=12).grid(row=r, column=1, sticky="w", pady=4)
        r += 1

        ttk.Label(parent, text="Grind").grid(row=r, column=0, sticky="w")
        ttk.Combobox(
            parent,
            textvariable=self.var_grind,
            values=["fine", "medium", "coarse"],
            state="readonly",
            width=12,
        ).grid(row=r, column=1, sticky="w", pady=4)
        r += 1

        ttk.Label(parent, text="Rating (1–10, opz.)").grid(row=r, column=0, sticky="w")
        self.entry_rating = ttk.Entry(parent, width=12)
        self.entry_rating.grid(row=r, column=1, sticky="w", pady=4)
        r += 1

        ttk.Label(parent, text="Notes (opz.)").grid(row=r, column=0, sticky="w")
        self.entry_notes = ttk.Entry(parent, width=28)
        self.entry_notes.grid(row=r, column=1, sticky="ew", pady=4)
        r += 1

        ttk.Label(parent, textvariable=self.var_water_preview, font=("Helvetica", 11, "bold")).grid(
            row=r, column=0, columnspan=2, sticky="w", pady=(10, 4)
        )
        r += 1

        btns = ttk.Frame(parent)
        btns.grid(row=r, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)

        ttk.Button(btns, text="Salva brew", command=self._on_save).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(btns, text="Ricarica storico", command=self._load_history).grid(row=0, column=1, sticky="ew")

        # Water preview: aggiorna quando dose/ratio cambiano
        self.var_dose.trace_add("write", lambda *_: self._update_water_preview())
        self.var_ratio.trace_add("write", lambda *_: self._update_water_preview())
        self._update_water_preview()

    def _build_table(self, parent: ttk.Frame) -> None:
        cols = ("id", "coffee", "dose", "ratio", "water", "temp", "grind", "rating", "notes")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=14)
        self.tree.grid(row=0, column=0, sticky="nsew")

        for c, label in [
            ("id", "ID"),
            ("coffee", "Coffee"),
            ("dose", "Dose (g)"),
            ("ratio", "Ratio"),
            ("water", "Water (ml)"),
            ("temp", "Temp (°C)"),
            ("grind", "Grind"),
            ("rating", "Rating"),
            ("notes", "Notes"),
        ]:
            self.tree.heading(c, text=label)

        self.tree.column("id", width=55, anchor="center")
        self.tree.column("coffee", width=170)
        self.tree.column("dose", width=85, anchor="e")
        self.tree.column("ratio", width=70, anchor="e")
        self.tree.column("water", width=95, anchor="e")
        self.tree.column("temp", width=85, anchor="e")
        self.tree.column("grind", width=90, anchor="center")
        self.tree.column("rating", width=75, anchor="center")
        self.tree.column("notes", width=260)

        yscroll = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        yscroll.grid(row=0, column=1, sticky="ns")

        actions = ttk.Frame(parent)
        actions.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        ttk.Button(actions, text="Elimina selezionato", command=self._on_delete_selected).pack(side="left")
        ttk.Button(actions, text="Refresh", command=self._load_history).pack(side="left", padx=(8, 0))

    # ---------- Helpers ----------
    def _parse_float(self, s: str, field: str) -> float:
        try:
            return float(s.strip().replace(",", "."))
        except Exception:
            raise ValueError(f"Valore non valido per {field}: {s!r}")

    def _parse_int_optional(self, s: str) -> int | None:
        s = s.strip()
        if not s:
            return None
        return int(s)

    def _update_water_preview(self) -> None:
        try:
            dose = self._parse_float(self.var_dose.get(), "dose")
            ratio = self._parse_float(self.var_ratio.get(), "ratio")
            water = round(dose * ratio, 1)
            self.var_water_preview.set(f"Acqua: {water} ml")
        except Exception:
            self.var_water_preview.set("Acqua: - ml")

    # ---------- Actions ----------
    def _on_save(self) -> None:
        # FIX DEFINITIVO: leggiamo direttamente dall'Entry widget
        coffee = self.entry_coffee.get().strip()
        print("DEBUG coffee =", repr(coffee))  # lascia per 1-2 prove

        if not coffee:
            messagebox.showerror("Errore", "Il campo Coffee è obbligatorio.")
            return

        try:
            dose = self._parse_float(self.var_dose.get(), "dose")
            ratio = self._parse_float(self.var_ratio.get(), "ratio")
            temp = int(self.var_temp.get().strip())
            grind = (self.var_grind.get().strip() or "medium")
            rating_raw = self.entry_rating.get().strip()
            rating = int(rating_raw) if rating_raw else None

            notes = self.entry_notes.get().strip() or None

            water = round(dose * ratio, 1)

            # validazioni minime
            if dose <= 0:
                raise ValueError("La dose deve essere > 0.")
            if not (10 <= ratio <= 25):
                raise ValueError("Ratio fuori range (consiglio 12–20).")
            if not (70 <= temp <= 100):
                raise ValueError("Temperatura fuori range (70–100).")
            if rating is not None and not (1 <= rating <= 10):
                raise ValueError("Rating deve essere tra 1 e 10.")
        except Exception as e:
            messagebox.showerror("Errore input", str(e))
            return

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

        messagebox.showinfo("Salvato", f"Brew salvata con ID #{b.id}")
        self._load_history()
        self._clear_form(keep_coffee=False)

    def _clear_form(self, keep_coffee: bool = False) -> None:
        if not keep_coffee:
            self.entry_coffee.delete(0, tk.END)
        self.var_dose.set("16")
        self.var_ratio.set("16")
        self.var_temp.set("94")
        self.var_grind.set("medium")
        self.var_rating.set("")
        self.var_notes.set("")
        self._update_water_preview()
        self.after(100, lambda: self.entry_coffee.focus_set())

    def _load_history(self) -> None:
        # pulisci tabella
        for item in self.tree.get_children():
            self.tree.delete(item)

        db = SessionLocal()
        try:
            rows = db.execute(select(Brew).order_by(Brew.id.desc()).limit(200)).scalars().all()
        finally:
            db.close()

        for b in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    b.id,
                    b.coffee,
                    b.dose,
                    b.ratio,
                    b.water,
                    b.temperature,
                    b.grind,
                    b.rating if b.rating is not None else "",
                    b.notes if b.notes is not None else "",
                ),
            )

    def _on_delete_selected(self) -> None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Attenzione", "Seleziona una riga da eliminare.")
            return

        item = sel[0]
        values = self.tree.item(item, "values")
        brew_id = int(values[0])

        if not messagebox.askyesno("Conferma", f"Eliminare brew #{brew_id}?"):
            return

        db = SessionLocal()
        try:
            b = db.get(Brew, brew_id)
            if b:
                db.delete(b)
                db.commit()
        finally:
            db.close()

        self._load_history()


def main() -> None:

    try:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass

    app = HoopGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
