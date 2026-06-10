# Vinaris Marketing Agent

Tool interno Python per generare, revisionare e gestire contenuti social di **Vinaris** tramite CLI e mini dashboard web.

## Obiettivo

Il progetto supporta il team Vinaris nella creazione di contenuti per:

- Facebook
- Instagram
- LinkedIn

Ogni contenuto viene salvato in SQLite con stato editoriale:

- `draft`
- `approved`
- `published`
- `rejected`

La pubblicazione reale non e ancora integrata: `publisher_stub.py` simula il passaggio a `published`.

## Brand Context

- Nome: `Vinaris`
- Payoff: `Private cellar intelligence`
- Target: appassionati e collezionisti privati di vino
- Tone of voice: premium, competente, sobrio, non aggressivo
- Lingua principale: italiano
- Prezzi beta: `CHF 6/mese`, `CHF 60/anno`
- Offerta beta tester: `2 mesi gratuiti escluso AI Pack`

## Struttura

```text
app/
data/
deploy/
exports/
generated_images/
```

## Requisiti

- Python 3.11+

## Installazione

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Configurazione

Variabili supportate:

- `OPENAI_API_KEY`: chiave OpenAI per testo e immagini
- `OPENAI_IMAGE_MODEL`: modello immagini, default `gpt-image-2`
- `OPENAI_IMAGE_QUALITY`: qualita immagini, default `medium`
- `OPENAI_IMAGE_FORMAT`: formato immagini, default `png`
- `VINARIS_DB_PATH`: path del database SQLite, default `data/posts.sqlite`
- `VINARIS_GENERATED_IMAGES_DIR`: cartella output immagini, default `generated_images`
- `VINARIS_EXPORTS_DIR`: cartella export manuali, default `exports`
- `VINARIS_WEB_SECRET`: secret key Flask per la dashboard
- `VINARIS_APP_ENV`: ambiente applicativo

Se `OPENAI_API_KEY` non e presente, il generatore testi usa contenuti mock realistici e la generazione immagini non viene eseguita.

## Comandi CLI

Generare 10 bozze:

```bash
python -m app.main generate --count 10
```

Generare post solo per Instagram:

```bash
python -m app.main generate --count 3 --platform Instagram
```

Generare post solo per una categoria specifica:

```bash
python -m app.main generate --count 2 --category "gestione cantina"
```

Generare post per piattaforma e categoria:

```bash
python -m app.main generate --count 2 --platform Instagram --category "beta tester"
```

Generare 10 bozze con immagine OpenAI per ciascuna:

```bash
python -m app.main generate --count 10 --with-images
```

Listare le bozze:

```bash
python -m app.main list --status draft
```

Mostrare il dettaglio di un post:

```bash
python -m app.main show --id 1
```

Approvare un post:

```bash
python -m app.main approve --id 1
```

Rifiutare un post:

```bash
python -m app.main reject --id 1
```

Generare o rigenerare l'immagine di un post:

```bash
python -m app.main render-image --id 1
```

Esportare un pack manuale per pubblicazione esterna:

```bash
python -m app.main export --id 1
```

Generare immagini in batch per tutte le bozze Instagram senza immagine:

```bash
python -m app.main render-batch --status draft --platform Instagram --only-missing
```

Simulare la pubblicazione:

```bash
python -m app.main publish --id 1
```

## Dashboard Web

Avvio rapido:

```bash
python -m flask --app app.web run --debug
```

Oppure:

```bash
python -m app.web
```

URL locale:

```text
http://127.0.0.1:5000
```

Funzioni disponibili nella dashboard:

- lista post con filtri per stato e piattaforma
- pagina dettaglio post
- generazione nuove bozze
- approvazione e rifiuto manuale
- pubblicazione simulata
- generazione immagine singola
- render batch immagini
- export pack per pubblicazione manuale

## Export Manuale

Il comando `export` crea una cartella dedicata per post, ad esempio:

```text
exports/post-8-instagram/
```

Contenuto:

- `caption.txt`
- `post.json`
- immagine generata, se disponibile

Questo e il formato pensato per:

- copia/incolla rapido della caption
- upload manuale su Instagram
- archiviazione interna del contenuto approvato

## Deploy Ubuntu

Installazione iniziale sul server:

```bash
git clone https://github.com/bariom/vinaris-marketing-agent.git
cd vinaris-marketing-agent
bash deploy/install_ubuntu.sh
```

Poi:

1. Compila `.env`
2. Avvia il servizio web

Avvio manuale con Gunicorn:

```bash
bash deploy/start_ubuntu.sh
```

La porta di default nello startup script e `8123`.

Update dal repository:

```bash
BRANCH=main bash deploy/update_ubuntu.sh
```

Se vuoi usare `systemd`, parti dal template:

```text
deploy/vinaris-marketing-agent.service.example
```

Protezione di `.env`:

- `.env` non viene versionato grazie a `.gitignore`
- `deploy/install_ubuntu.sh` forza `chmod 600 .env`
- le cartelle `data/`, `generated_images/` ed `exports/` vengono create con permessi stretti
- se usi Nginx, nega l'accesso ai dotfile con il template:

```text
deploy/nginx.vinaris-marketing-agent.conf.example
```

## Note tecniche

- Storage basato su SQLite
- CLI costruita con `argparse`
- Dashboard interna costruita con Flask
- Codice tipizzato con type hints
- Fallback automatico a contenuti mock se OpenAI non e configurato o non disponibile
- Architettura pronta per future integrazioni API social
- Integrazione immagini via OpenAI Image API
