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
  __init__.py
  brand_profile.py
  config.py
  content_generator.py
  image_prompt_generator.py
  image_renderer.py
  main.py
  platform_profiles.py
  publisher_stub.py
  social_calendar.py
  static/
  storage.py
  templates/
  web.py
  workflows.py
data/
  posts.sqlite
generated_images/
.env.example
deploy/
requirements.txt
README.md
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
- `VINARIS_WEB_SECRET`: secret key Flask per la dashboard
- `VINARIS_APP_ENV`: ambiente applicativo

Se `OPENAI_API_KEY` non e presente, il generatore testi usa contenuti mock realistici e la generazione immagini non viene eseguita.

## Comandi CLI

Generare 10 bozze:

```bash
python -m app.main generate --count 10
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

Generare immagini in batch per tutte le bozze Instagram senza immagine:

```bash
python -m app.main render-batch --status draft --platform Instagram --only-missing
```

Generare immagini in batch con limite:

```bash
python -m app.main render-batch --status draft --limit 5 --only-missing
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

Update dal repository:

```bash
BRANCH=main bash deploy/update_ubuntu.sh
```

Se vuoi usare `systemd`, parti dal template:

```text
deploy/vinaris-marketing-agent.service.example
```

Esempio rapido:

```bash
sudo cp deploy/vinaris-marketing-agent.service.example /etc/systemd/system/vinaris-marketing-agent.service
sudo systemctl daemon-reload
sudo systemctl enable vinaris-marketing-agent
sudo systemctl start vinaris-marketing-agent
sudo systemctl status vinaris-marketing-agent
```

## Cosa genera

Ogni post contiene:

- piattaforma
- formato consigliato per piattaforma
- titolo interno
- testo breve
- testo medio
- CTA
- hashtag
- prompt immagine
- path immagine generata, se disponibile
- stato
- data creazione
- data pianificata

## Formati per canale

Il progetto salva anche un formato visuale consigliato per canale:

- Instagram: `4:5` con size target `1024x1280`
- Facebook: `1.91:1` con size target `1536x800`
- LinkedIn: `1.91:1` con size target `1536x800`

Questo dato viene usato per:

- arricchire il `image_prompt`
- guidare OpenAI nella generazione
- rendere piu chiaro il target asset in CLI e dashboard

## Note tecniche

- Storage basato su SQLite
- CRUD base in `app/storage.py`
- CLI costruita con `argparse`
- Dashboard interna costruita con Flask
- Codice tipizzato con type hints
- Fallback automatico a contenuti mock se OpenAI non e configurato o non disponibile
- Architettura pronta per future integrazioni API social
- Integrazione immagini via OpenAI Image API

## Roadmap

- Integrazione Meta Graph API
- Integrazione LinkedIn API
- Varianti multi-formato immagini per Stories e ads
- Editing contenuti direttamente da dashboard web
- Calendario editoriale piu avanzato
- Metriche performance dei contenuti
- Versioning dei contenuti e storico revisioni

## Note OpenAI

Secondo la documentazione ufficiale OpenAI, l'API immagini consente di generare immagini da prompt testuali usando modelli GPT Image, incluso `gpt-image-2`, e per richieste singole il percorso consigliato e l'Image API. Le immagini dei modelli GPT Image vengono restituite in base64 e possono essere salvate localmente dal client Python. Fonti:

- https://developers.openai.com/api/docs/guides/image-generation
- https://developers.openai.com/api/reference/resources/images/methods/generate/
