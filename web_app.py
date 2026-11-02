from email import policy
from email.parser import BytesParser
import io
import json
import subprocess
import tempfile
import zipfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from converter_excel_pdf import find_libreoffice


ROOT = Path(__file__).parent
WEB_ROOT = ROOT / "web"
MAX_UPLOAD_BYTES = 100 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".xlsm", ".xlsb"}


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_GET(self):
        if urlparse(self.path).path == "/download/linux":
            package = ROOT / "dist" / "fogli-in-pdf_1.0.0_amd64.deb"
            if not package.is_file():
                self.send_json(404, {"error": "Pacchetto Linux non disponibile."})
                return
            data = package.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.debian.binary-package")
            self.send_header("Content-Disposition", 'attachment; filename="fogli-in-pdf_1.0.0_amd64.deb"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path != "/convert":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_UPLOAD_BYTES:
                self.send_json(400, {"error": "Seleziona file per un massimo di 100 MB."})
                return

            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                self.send_json(400, {"error": "Formato della richiesta non valido."})
                return

            headers = (
                f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("ascii")
            )
            message = BytesParser(policy=policy.default).parsebytes(headers + self.rfile.read(length))
            if not message.is_multipart():
                raise ValueError("Formato della richiesta non valido.")
            uploads = [
                (part.get_filename(), part.get_payload(decode=True) or b"")
                for part in message.iter_parts()
                if part.get_filename() and part.get_param("name", header="content-disposition") == "files"
            ]
            if not uploads:
                self.send_json(400, {"error": "Seleziona almeno un file Excel."})
                return

            office = find_libreoffice()
            if not office:
                self.send_json(503, {"error": "LibreOffice non è disponibile sul server."})
                return

            archive = self.convert_uploads(office, uploads)
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", 'attachment; filename="file-convertiti.zip"')
            self.send_header("Content-Length", str(len(archive)))
            self.end_headers()
            self.wfile.write(archive)
        except ValueError as error:
            self.send_json(400, {"error": str(error)})
        except Exception as error:
            self.send_json(500, {"error": f"Conversione non riuscita: {error}"})

    def convert_uploads(self, office, uploads):
        archive_data = io.BytesIO()
        used_names = set()

        with tempfile.TemporaryDirectory(prefix="excel-pdf-web-") as temporary:
            temporary_path = Path(temporary)
            input_folder = temporary_path / "input"
            output_folder = temporary_path / "output"
            input_folder.mkdir()
            output_folder.mkdir()

            for index, (original_name, content) in enumerate(uploads, start=1):
                filename = Path(original_name.replace("\\", "/")).name
                suffix = Path(filename).suffix.lower()
                if suffix not in SUPPORTED_EXTENSIONS:
                    raise ValueError(f"Formato non supportato: {filename}")
                if not content:
                    raise ValueError(f"Il file è vuoto: {filename}")

                source = input_folder / f"{index}{suffix}"
                source.write_bytes(content)
                profile = (temporary_path / f"profile-{index}").as_uri()
                result = subprocess.run(
                    [
                        office,
                        "--headless",
                        f"-env:UserInstallation={profile}",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        str(output_folder),
                        str(source),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=180,
                    check=False,
                )
                pdf_path = output_folder / f"{index}.pdf"
                if result.returncode != 0 or not pdf_path.is_file():
                    detail = result.stderr.strip() or result.stdout.strip() or "errore di conversione"
                    raise ValueError(f"{filename}: {detail}")

                pdf_name = f"{Path(filename).stem}.pdf"
                candidate = pdf_name
                counter = 2
                while candidate in used_names:
                    candidate = f"{Path(filename).stem} ({counter}).pdf"
                    counter += 1
                used_names.add(candidate)
                with zipfile.ZipFile(archive_data, "a", zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr(candidate, pdf_path.read_bytes())

        return archive_data.getvalue()

    def send_json(self, status, data):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), AppHandler)
    print("App pronta: http://localhost:8000")
    server.serve_forever()
