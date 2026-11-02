import os
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


def find_libreoffice():
    executable_dir = Path(sys.executable).resolve().parent
    if sys.platform == "win32":
        candidate = executable_dir / "LibreOffice" / "program" / "soffice.exe"
        if candidate.is_file():
            return str(candidate)
    elif sys.platform == "darwin":
        resources = executable_dir.parent / "Resources"
        candidate = resources / "LibreOffice.app" / "Contents" / "MacOS" / "soffice"
        if candidate.is_file():
            return str(candidate)

    executable = shutil.which("soffice") or shutil.which("libreoffice")
    if executable:
        return executable

    if sys.platform == "win32":
        for variable in ("ProgramFiles", "ProgramFiles(x86)"):
            base = os.environ.get(variable)
            if base:
                candidate = Path(base) / "LibreOffice" / "program" / "soffice.exe"
                if candidate.is_file():
                    return str(candidate)
    elif sys.platform == "darwin":
        candidate = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
        if candidate.is_file():
            return str(candidate)

    return None


class ExcelPdfConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Convertitore Excel in PDF")
        self.root.minsize(540, 330)
        self.files = []
        self.output_folder = tk.StringVar()
        self.status = tk.StringVar(value="Seleziona i file Excel da convertire.")

        main = ttk.Frame(root, padding=20)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Convertitore Excel in PDF", font=("TkDefaultFont", 16, "bold")).pack(anchor="w")
        ttk.Label(main, text="Converti più fogli di lavoro in una sola volta.").pack(anchor="w", pady=(4, 16))

        file_row = ttk.Frame(main)
        file_row.pack(fill="x")
        self.file_button = ttk.Button(file_row, text="Seleziona file Excel", command=self.select_files)
        self.file_button.pack(side="left")
        self.file_label = ttk.Label(file_row, text="Nessun file selezionato")
        self.file_label.pack(side="left", padx=10)

        output_row = ttk.Frame(main)
        output_row.pack(fill="x", pady=(18, 12))
        ttk.Label(output_row, text="Cartella di destinazione").pack(anchor="w")
        path_row = ttk.Frame(output_row)
        path_row.pack(fill="x", pady=(5, 0))
        ttk.Entry(path_row, textvariable=self.output_folder, state="readonly").pack(side="left", fill="x", expand=True)
        self.folder_button = ttk.Button(path_row, text="Sfoglia...", command=self.select_output_folder)
        self.folder_button.pack(side="left", padx=(8, 0))

        self.convert_button = ttk.Button(main, text="Converti in PDF", command=self.convert_files)
        self.convert_button.pack(anchor="w", pady=(4, 12))
        ttk.Label(main, textvariable=self.status, wraplength=490).pack(anchor="w")

    def select_files(self):
        selected = filedialog.askopenfilenames(
            title="Seleziona i file Excel",
            filetypes=[("File Excel", "*.xlsx *.xls *.xlsm *.xlsb"), ("Tutti i file", "*.*")],
        )
        if selected:
            self.files = [Path(path) for path in selected]
            self.file_label.configure(text=f"{len(self.files)} file selezionati")
            self.status.set("Scegli la cartella di destinazione e avvia la conversione.")

    def select_output_folder(self):
        selected = filedialog.askdirectory(title="Scegli la cartella di destinazione")
        if selected:
            self.output_folder.set(selected)

    def convert_files(self):
        if not self.files:
            messagebox.showwarning("File mancanti", "Seleziona almeno un file Excel.")
            return
        if not self.output_folder.get():
            messagebox.showwarning("Cartella mancante", "Scegli la cartella in cui salvare i PDF.")
            return

        office = find_libreoffice()
        if not office:
            messagebox.showerror(
                "LibreOffice non trovato",
                "Installa LibreOffice per convertire i file, poi riavvia l'applicazione.",
            )
            return

        self.set_busy(True)
        self.status.set("Conversione in corso...")
        threading.Thread(target=self.run_conversion, args=(office,), daemon=True).start()

    def run_conversion(self, office):
        destination = Path(self.output_folder.get())
        completed = 0
        errors = []

        for index, source in enumerate(self.files, start=1):
            try:
                with tempfile.TemporaryDirectory(prefix="excel-to-pdf-") as temporary:
                    temporary_path = Path(temporary)
                    converted_folder = temporary_path / "converted"
                    converted_folder.mkdir()
                    command = [
                        office,
                        "--headless",
                        f"-env:UserInstallation={(temporary_path / 'profile').as_uri()}",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        str(converted_folder),
                        str(source),
                    ]
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=180,
                        check=False,
                    )
                    converted_file = converted_folder / f"{source.stem}.pdf"
                    if result.returncode != 0 or not converted_file.is_file():
                        detail = result.stderr.strip() or result.stdout.strip() or "conversione non riuscita"
                        raise RuntimeError(detail)

                    target = self.unique_destination(destination, converted_file.name)
                    shutil.move(str(converted_file), str(target))
                    completed += 1
            except Exception as error:
                errors.append(f"{source.name}: {error}")

            self.root.after(0, self.update_progress, index, len(self.files))

        self.root.after(0, self.show_results, completed, errors)

    @staticmethod
    def unique_destination(folder, filename):
        target = folder / filename
        counter = 2
        while target.exists():
            target = folder / f"{Path(filename).stem} ({counter}).pdf"
            counter += 1
        return target

    def update_progress(self, current, total):
        self.status.set(f"Convertiti {current} di {total} file...")

    def show_results(self, completed, errors):
        self.set_busy(False)
        if errors:
            details = "\n".join(errors[:5])
            if len(errors) > 5:
                details += f"\n... e altri {len(errors) - 5} errori."
            self.status.set(f"Completati: {completed}. Errori: {len(errors)}.")
            messagebox.showwarning("Conversione terminata", f"PDF creati: {completed}\n\n{details}")
        else:
            self.status.set(f"Conversione completata: {completed} PDF salvati.")
            messagebox.showinfo("Conversione completata", f"Creati {completed} file PDF.")

    def set_busy(self, busy):
        state = "disabled" if busy else "normal"
        self.file_button.configure(state=state)
        self.folder_button.configure(state=state)
        self.convert_button.configure(state=state)


if __name__ == "__main__":
    application = tk.Tk()
    ExcelPdfConverter(application)
    application.mainloop()