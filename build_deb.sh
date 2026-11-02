#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PACKAGE_ROOT=$(mktemp -d)
trap 'rm -rf "$PACKAGE_ROOT"' EXIT

install -d "$PACKAGE_ROOT/DEBIAN"
install -d "$PACKAGE_ROOT/usr/lib/fogli-in-pdf"
install -d "$PACKAGE_ROOT/usr/bin"
install -d "$PACKAGE_ROOT/usr/share/applications"
install -m 644 "$ROOT/packaging/debian/control" "$PACKAGE_ROOT/DEBIAN/control"
install -m 644 "$ROOT/converter_excel_pdf.py" "$PACKAGE_ROOT/usr/lib/fogli-in-pdf/converter_excel_pdf.py"
install -m 755 "$ROOT/packaging/debian/fogli-in-pdf" "$PACKAGE_ROOT/usr/bin/fogli-in-pdf"
install -m 644 "$ROOT/packaging/debian/fogli-in-pdf.desktop" "$PACKAGE_ROOT/usr/share/applications/fogli-in-pdf.desktop"
chmod -R a+rX "$PACKAGE_ROOT"
chmod 755 "$PACKAGE_ROOT"

mkdir -p "$ROOT/dist"
dpkg-deb --build --root-owner-group "$PACKAGE_ROOT" "$ROOT/dist/fogli-in-pdf_1.0.0_amd64.deb"
printf 'Pacchetto creato: %s\n' "$ROOT/dist/fogli-in-pdf_1.0.0_amd64.deb"