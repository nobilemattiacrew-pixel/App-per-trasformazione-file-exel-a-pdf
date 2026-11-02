# Convertitore Excel in PDF

Applicazione web locale per convertire più file Excel in PDF. Seleziona o trascina i file nell'interfaccia, poi scarica i PDF raccolti in un archivio ZIP. I file vengono elaborati dal backend Python con LibreOffice.

## Requisiti

- Python 3
- LibreOffice installato e disponibile come `soffice`

## Windows e macOS

Gli installer nativi vengono creati su runner Windows e macOS da GitHub Actions. Per generarli, avvia **Build desktop installers** dalla scheda **Actions** oppure crea e pubblica un tag `v*`; il workflow pubblica gli eseguibili nella release GitHub. Entrambi includono LibreOffice.

Il DMG macOS non è firmato/notarizzato: al primo avvio potrebbe essere necessario autorizzare l'app da **Impostazioni di Sistema > Privacy e Sicurezza**.

## Ubuntu/Debian (64 bit)

Avvia il server web con `python3 web_app.py` e scarica il pacchetto dal pulsante **Scarica app Linux** oppure da `http://localhost:8000/download/linux`. In Codespaces apri la porta 8000 dal pannello **Ports**.

Installa il file `.deb` scaricato con:

```bash
sudo apt install ./fogli-in-pdf_1.0.0_amd64.deb
```

Il pacchetto dichiara Python, Tkinter e LibreOffice come dipendenze; `apt` li installa se mancano. Dopo l'installazione avvia **Fogli in PDF** dal menu applicazioni oppure esegui `fogli-in-pdf`.

Per rigenerare il pacchetto dal sorgente, esegui `./build_deb.sh`. Il pacchetto viene creato in `dist/`.

## Avvio dell'interfaccia web

```bash
python3 web_app.py
```

Apri `http://localhost:8000`. In Codespaces, apri la porta `8000` dalla scheda **Ports** per visualizzare l'app nel browser.

L'app supporta `.xlsx`, `.xls`, `.xlsm` e `.xlsb`, con un limite totale di 100 MB per caricamento. Non richiede pacchetti Python aggiuntivi.

## Interfaccia desktop

Su un computer con interfaccia grafica puoi avviare anche la versione desktop:

```bash
python3 converter_excel_pdf.py
```