import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "skovoroTka.db")


def qident(name: str) -> str:
    """Quote SQL identifiers safely with double quotes."""
    return '"' + name.replace('"', '""') + '"'


class DbApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('SIA "SkovoroTka" — DB GUI (Tkinter + SQLite)')
        self.geometry("1200x700")
        self.minsize(1050, 620)

        if not os.path.exists(DB_PATH):
            messagebox.showerror(
                "DB nav atrasta",
                f"Nevar atrast datubāzi:\n{DB_PATH}\n\nIeliec skovoroTka.db blakus app.py."
            )
            raise FileNotFoundError(DB_PATH)

        self.con = sqlite3.connect(DB_PATH)
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()

        
        tables = [r[0] for r in self.cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        ).fetchall()]

        messagebox.showinfo(
            "DB info",
            "Atvērta datubāze:\n"
            f"{DB_PATH}\n\n"
            "Tabulas:\n- " + "\n- ".join(tables)
        )

        if "Klienti" not in tables:
            messagebox.showerror(
                "Nepareiza datubāze",
                "Šajā DB nav tabulas 'Klienti'.\n\n"
                "Tas nozīmē, ka tu atvēri nepareizu skovoroTka.db (parasti tukšu DB).\n"
                "Izdzēs šo skovoroTka.db un ieliec pareizo (ar tabulām), vai pārliecinies, ka DB ir blakus app.py.\n\n"
                f"Ceļš: {DB_PATH}\n"
                f"Tabulas: {tables}"
            )
            self.con.close()
            self.destroy()
            return

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)

        self._build_tabs()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        try:
            self.con.commit()
            self.con.close()
        finally:
            self.destroy()

    def run(self, sql: str, params=()):
        try:
            self.cur.execute(sql, params)
            self.con.commit()
            return self.cur
        except Exception as e:
            messagebox.showerror("DB error", f"{e}\n\nSQL:\n{sql}\n\nParams:\n{params}")
            return None

    def fetchall(self, sql: str, params=()):
        cur = self.run(sql, params)
        if not cur:
            return []
        return cur.fetchall()

    def _build_tabs(self):
        self.nb.add(CrudTab(
            master=self.nb,
            app=self,
            title="Klienti",
            table="Klienti",
            pk="klients_id",
            columns=[
                ("vards", "Vārds"),
                ("uzvards", "Uzvārds"),
                ("telefons", "Telefons"),
                ("alergijas", "Alerģijas"),
            ],
        ), text="Klienti")

        self.nb.add(CrudTab(
            master=self.nb,
            app=self,
            title="Darbinieki",
            table="Darbinieki",
            pk="darbinieks_id",
            columns=[
                ("vards", "Vārds"),
                ("uzvards", "Uzvārds"),
                ("vecums", "Vecums"),
                ("pieredze", "Pieredze"),
            ],
        ), text="Darbinieki")

        self.nb.add(CrudTab(
            master=self.nb,
            app=self,
            title="Pasutijumi",
            table="Pasutijumi",
            pk="pasutijums_id",
            columns=[
                ("laiks", "Laiks"),
                ("galds", "Galds"),
                ("klients_id", "Klients ID"),
                ("darbinieks_id", "Darbinieks ID"),
            ],
        ), text="Pasūtījumi")

        self.nb.add(CrudTab(
            master=self.nb,
            app=self,
            title="Pamatedieni",
            table="Pamatedieni",
            pk="pamatediens_id",
            columns=[
                ("nosaukums", "Nosaukums"),
                ("daudzums", "Daudzums"),
                ("kategorija_id", "Kategorija ID"),
                ("pasutijums_id", "Pasutijums ID"),
            ],
        ), text="Pamatēdieni")

        self.nb.add(CrudTab(
            master=self.nb,
            app=self,
            title="Deserti",
            table="Deserti",
            pk="deserts_id",
            columns=[
                ("nosaukums", "Nosaukums"),
                ("daudzums", "Daudzums"),
                ("kategorija_id", "Kategorija ID"),
                ("pasutijums_id", "Pasutijums ID"),
            ],
        ), text="Deserti")

        self.nb.add(CrudTab(
            master=self.nb,
            app=self,
            title="Dzerieni",
            table="Dzerieni",
            pk="dzeriens_id",
            columns=[
                ("nosaukums", "Nosaukums"),
                ("daudzums", "Daudzums"),
                ("alkohols", "Alkohols (jā/nē)"),
                ("kategorija_id", "Kategorija ID"),
                ("pasutijums_id", "Pasutijums ID"),
            ],
        ), text="Dzērieni")

        self.nb.add(CrudTab(
            master=self.nb,
            app=self,
            title="Kategorijas",
            table="Kategorijas",
            pk="kategorija_id",
            columns=[
                ("pamatediens", "Kategorija pamatēdieni"),
                ("deserts", "Kategorija deserti"),
                ("dzeriens", "Kategorija dzērieni"),
                ("cena", "Cena"),
            ],
        ), text="Kategorijas")

        # self.nb.add(QueriesTab(master=self.nb, app=self), text="Vaicājumi / Filtri")


class CrudTab(ttk.Frame):
    def __init__(self, master, app: DbApp, title: str, table: str, pk: str, columns):
        super().__init__(master)
        self.app = app
        self.title = title
        self.table = table
        self.pk = pk
        self.columns = columns
        self.selected_pk = None

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        form = ttk.LabelFrame(self, text=f"{self.title} — forma")
        form.pack(fill="x", padx=10, pady=10)

        self.entries = {}
        for i, (col, label) in enumerate(self.columns):
            ttk.Label(form, text=label).grid(row=0, column=2*i, sticky="w", padx=(10, 4), pady=8)
            ent = ttk.Entry(form, width=22)
            ent.grid(row=0, column=2*i+1, sticky="w", padx=(0, 10), pady=8)
            self.entries[col] = ent

        btns = ttk.Frame(form)
        btns.grid(row=1, column=0, columnspan=999, sticky="w", padx=10, pady=(0, 10))

        ttk.Button(btns, text="Pievienot (INSERT)", command=self.insert).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Atjaunot (UPDATE)", command=self.update).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Dzēst (DELETE)", command=self.delete).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Notīrīt formu", command=self.clear_form).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Refresh", command=self.refresh).pack(side="left")

        search = ttk.Frame(self)
        search.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Label(search, text="Meklēt (teksts):").pack(side="left")
        self.search_var = tk.StringVar()
        ttk.Entry(search, textvariable=self.search_var, width=40).pack(side="left", padx=8)
        ttk.Button(search, text="Meklēt", command=self.refresh).pack(side="left")
        ttk.Button(search, text="Parādīt visu", command=self._reset_search).pack(side="left", padx=8)

        tv_frame = ttk.Frame(self)
        tv_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        cols = [self.pk] + [c for c, _ in self.columns]
        self.tv = ttk.Treeview(tv_frame, columns=cols, show="headings")

        for c in cols:
            self.tv.heading(c, text=c)
            self.tv.column(c, width=165, anchor="w")
        self.tv.column(self.pk, width=110, anchor="center")

        ysb = ttk.Scrollbar(tv_frame, orient="vertical", command=self.tv.yview)
        xsb = ttk.Scrollbar(tv_frame, orient="horizontal", command=self.tv.xview)
        self.tv.configure(yscroll=ysb.set, xscroll=xsb.set)

        self.tv.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")

        tv_frame.rowconfigure(0, weight=1)
        tv_frame.columnconfigure(0, weight=1)

        self.tv.bind("<<TreeviewSelect>>", self.on_select)

    def _reset_search(self):
        self.search_var.set("")
        self.refresh()

    def clear_form(self):
        self.selected_pk = None
        for ent in self.entries.values():
            ent.delete(0, tk.END)
        self.tv.selection_remove(self.tv.selection())

    def on_select(self, _evt):
        sel = self.tv.selection()
        if not sel:
            return
        item = self.tv.item(sel[0])
        values = item["values"]
        self.selected_pk = values[0]
        for (col, _label), v in zip(self.columns, values[1:]):
            ent = self.entries[col]
            ent.delete(0, tk.END)
            ent.insert(0, "" if v is None else str(v))

    def refresh(self):
        for i in self.tv.get_children():
            self.tv.delete(i)

        where = ""
        params = []
        q = self.search_var.get().strip()
        if q:
            likes = []
            for col, _ in self.columns:
                likes.append(f"CAST({qident(col)} AS TEXT) LIKE ?")
                params.append(f"%{q}%")
            where = "WHERE " + " OR ".join(likes)

        sql = (
            f"SELECT {qident(self.pk)}, " +
            ", ".join([qident(c) for c, _ in self.columns]) +
            f" FROM {qident(self.table)} {where} ORDER BY {qident(self.pk)} DESC"
        )

        rows = self.app.fetchall(sql, params)
        for r in rows:
            self.tv.insert("", "end", values=[r[self.pk]] + [r[c] for c, _ in self.columns])

    def insert(self):
        cols = [c for c, _ in self.columns]
        values = [self.entries[c].get().strip() for c in cols]
        if any(v == "" for v in values):
            messagebox.showwarning("Nepietiek dati", "Aizpildi visus laukus pirms INSERT.")
            return

        placeholders = ", ".join(["?"] * len(values))
        sql = (
            f"INSERT INTO {qident(self.table)} (" +
            ", ".join([qident(c) for c in cols]) +
            f") VALUES ({placeholders})"
        )
        if self.app.run(sql, values):
            self.clear_form()
            self.refresh()

    def update(self):
        if self.selected_pk is None:
            messagebox.showinfo("Nav izvēlēts ieraksts", "Izvēlies rindu tabulā, lai veiktu UPDATE.")
            return

        cols = [c for c, _ in self.columns]
        values = [self.entries[c].get().strip() for c in cols]
        if any(v == "" for v in values):
            messagebox.showwarning("Nepietiek dati", "Aizpildi visus laukus pirms UPDATE.")
            return

        sets = ", ".join([f"{qident(c)}=?" for c in cols])
        sql = f"UPDATE {qident(self.table)} SET {sets} WHERE {qident(self.pk)}=?"
        params = values + [self.selected_pk]
        if self.app.run(sql, params):
            self.clear_form()
            self.refresh()

    def delete(self):
        if self.selected_pk is None:
            messagebox.showinfo("Nav izvēlēts ieraksts", "Izvēlies rindu tabulā, lai veiktu DELETE.")
            return
        if not messagebox.askyesno("Apstiprināt", f"Dzēst ierakstu {self.pk}={self.selected_pk}?"):
            return

        sql = f"DELETE FROM {qident(self.table)} WHERE {qident(self.pk)}=?"
        if self.app.run(sql, (self.selected_pk,)):
            self.clear_form()
            self.refresh()


# class QueriesTab(ttk.Frame):
#     def __init__(self, master, app: DbApp):
#         super().__init__(master)
#         self.app = app
#         self._build_ui()

#     def _build_ui(self):
#         top = ttk.LabelFrame(self, text="SQL vaicājumi + filtri")
#         top.pack(fill="x", padx=10, pady=10)

#         self.query_var = tk.StringVar(value="q1")
#         items = [
#             ("q1", "1) SELECT * FROM Klienti"),
#             ("q2", "2) SELECT * FROM Klienti ORDER BY vards ASC"),
#             ("q3", "3) TOP 3 cenas no Kategorijas (ORDER BY cena DESC LIMIT 3)"),
#             ("q4", "4) JOIN Darbinieki + Pasutijumi (galds=7)"),
#             ("q5", "5) JOIN 3 tabulas: Pasutijumi + Klienti + Darbinieki"),
#         ]
#         for key, label in items:
#             ttk.Radiobutton(top, text=label, variable=self.query_var, value=key).pack(anchor="w", padx=10, pady=3)

#         btns = ttk.Frame(top)
#         btns.pack(fill="x", padx=10, pady=(8, 10))
#         ttk.Button(btns, text="RUN", command=self.run_selected).pack(side="left")
#         ttk.Button(btns, text="Clear", command=self.clear).pack(side="left", padx=8)

#         filt = ttk.LabelFrame(self, text="Filtri pēc veida")
#         filt.pack(fill="x", padx=10, pady=(0, 10))

#         ttk.Button(filt, text="Pasūtījumi ar Pamatēdieniem", command=self.filter_main_dishes).pack(side="left", padx=8, pady=8)
#         ttk.Button(filt, text="Pasūtījumi ar Desertiem", command=self.filter_desserts).pack(side="left", padx=8, pady=8)
#         ttk.Button(filt, text="Pasūtījumi ar Dzērieniem", command=self.filter_drinks).pack(side="left", padx=8, pady=8)

#         self.result = tk.Text(self, height=20, wrap="none")
#         self.result.pack(fill="both", expand=True, padx=10, pady=(0, 10))

#     def clear(self):
#         self.result.delete("1.0", tk.END)

#     def _print_rows(self, sql: str, rows):
#         self.clear()
#         self.result.insert(tk.END, "SQL:\n")
#         self.result.insert(tk.END, sql.strip() + "\n\n")
#         self.result.insert(tk.END, f"Rows: {len(rows)}\n")
#         self.result.insert(tk.END, "-" * 120 + "\n")
#         if not rows:
#             self.result.insert(tk.END, "(nav rezultātu)\n")
#             return
#         headers = rows[0].keys()
#         self.result.insert(tk.END, " | ".join(headers) + "\n")
#         self.result.insert(tk.END, "-" * 120 + "\n")
#         for r in rows:
#             self.result.insert(tk.END, " | ".join(str(r[h]) for h in headers) + "\n")

#     def run_selected(self):
#         key = self.query_var.get()
#         sql_map = {
#             "q1": (f"SELECT * FROM {qident('Klienti')};", ()),
#             "q2": (f"SELECT * FROM {qident('Klienti')} ORDER BY {qident('vards')} ASC;", ()),
#             "q3": (f"SELECT {qident('cena')} FROM {qident('Kategorijas')} ORDER BY {qident('cena')} DESC LIMIT 3;", ()),
#             "q4": (
#                 f"""
#                 SELECT d.{qident('vards')}, d.{qident('uzvards')}, d.{qident('pieredze')}, p.{qident('galds')}
#                 FROM {qident('Darbinieki')} d
#                 JOIN {qident('Pasutijumi')} p ON d.{qident('darbinieks_id')} = p.{qident('darbinieks_id')}
#                 WHERE p.{qident('galds')} = ?;
#                 """,
#                 ("7",),
#             ),
#             "q5": (
#                 f"""
#                 SELECT *
#                 FROM {qident('Pasutijumi')} p
#                 JOIN {qident('Klienti')} k ON k.{qident('klients_id')} = p.{qident('klients_id')}
#                 JOIN {qident('Darbinieki')} d ON d.{qident('darbinieks_id')} = p.{qident('darbinieks_id')};
#                 """,
#                 (),
#             ),
#         }
#         sql, params = sql_map[key]
#         rows = self.app.fetchall(sql, params)
#         self._print_rows(sql, rows)

#     def filter_main_dishes(self):
#         sql = f"""
#         SELECT p.{qident('pasutijums_id')}, p.{qident('laiks')}, p.{qident('galds')},
#                m.{qident('nosaukums')} AS pamatediens, m.{qident('daudzums')}
#         FROM {qident('Pasutijumi')} p
#         JOIN {qident('Pamatedieni')} m ON m.{qident('pasutijums_id')} = p.{qident('pasutijums_id')}
#         ORDER BY p.{qident('pasutijums_id')} DESC;
#         """
#         rows = self.app.fetchall(sql)
#         self._print_rows(sql, rows)

#     def filter_desserts(self):
#         sql = f"""
#         SELECT p.{qident('pasutijums_id')}, p.{qident('laiks')}, p.{qident('galds')},
#                d.{qident('nosaukums')} AS deserts, d.{qident('daudzums')}
#         FROM {qident('Pasutijumi')} p
#         JOIN {qident('Deserti')} d ON d.{qident('pasutijums_id')} = p.{qident('pasutijums_id')}
#         ORDER BY p.{qident('pasutijums_id')} DESC;
#         """
#         rows = self.app.fetchall(sql)
#         self._print_rows(sql, rows)

#     def filter_drinks(self):
#         sql = f"""
#         SELECT p.{qident('pasutijums_id')}, p.{qident('laiks')}, p.{qident('galds')},
#                z.{qident('nosaukums')} AS dzeriens, z.{qident('daudzums')}, z.{qident('alkohols')}
#         FROM {qident('Pasutijumi')} p
#         JOIN {qident('Dzerieni')} z ON z.{qident('pasutijums_id')} = p.{qident('pasutijums_id')}
#         ORDER BY p.{qident('pasutijums_id')} DESC;
#         """
#         rows = self.app.fetchall(sql)
#         self._print_rows(sql, rows)


if __name__ == "__main__":
    app = DbApp()
    app.mainloop()
