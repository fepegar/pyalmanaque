# PyAlmanaque

A web app that displays today's date in the [French Republican Calendar](https://en.wikipedia.org/wiki/French_Republican_calendar), along with an image and Wikipedia link for each day's associated plant, animal, tool, or mineral.

**Live at [pyalmanaque.azurewebsites.net](https://pyalmanaque.azurewebsites.net)**

## The French Republican Calendar

The French Republican Calendar (*calendrier républicain français*) was introduced by the National Convention on 24 October 1793 and used officially in France from 22 September 1792 (retroactively declared Year I) until 31 December 1805, when Napoleon reverted to the Gregorian calendar. It was designed to replace the Gregorian calendar's religious roots — named saints, seven-day weeks tied to Genesis — with a system grounded in nature, agriculture, and reason.

### Structure

The calendar has **12 months** of exactly **30 days** each, totaling 360 days. The remaining 5 days (6 in leap years) are the **Sansculottides** (*jours complémentaires*), placed at the end of the year as national festivals. There are no months of unequal length, no irregular leap-day insertions mid-year.

Each month is divided into three **décades** — 10-day weeks that replaced the 7-day week. The days within each décade are numbered rather than named after gods or planets:

| Day | Name | Position |
|-----|------|----------|
| 1st | Primidi | |
| 2nd | Duodi | |
| 3rd | Tridi | |
| 4th | Quartidi | |
| 5th | **Quintidi** | Animal day |
| 6th | Sextidi | |
| 7th | Septidi | |
| 8th | Octidi | |
| 9th | Nonidi | |
| 10th | **Décadi** | Tool day (rest day) |

The year begins at the **autumn equinox** (around 22 September in the Gregorian calendar), which is both astronomically precise and symbolically tied to the founding of the French Republic on 22 September 1792.

### Months and seasons

The month names, coined by Fabre d'Églantine, evoke the climate and agricultural character of each period. They rhyme in groups of three within each season:

| Season | Month | Translation | Approx. Gregorian |
|--------|-------|-------------|-------------------|
| **Autumn** | Vendémiaire | Grape harvest | Sep 22 – Oct 21 |
| | Brumaire | Fog | Oct 22 – Nov 20 |
| | Frimaire | Frost | Nov 21 – Dec 20 |
| **Winter** | Nivôse | Snow | Dec 21 – Jan 19 |
| | Pluviôse | Rain | Jan 20 – Feb 18 |
| | Ventôse | Wind | Feb 19 – Mar 20 |
| **Spring** | Germinal | Germination | Mar 21 – Apr 19 |
| | Floréal | Flowers | Apr 20 – May 19 |
| | Prairial | Meadows | May 20 – Jun 18 |
| **Summer** | Messidor | Harvest | Jun 19 – Jul 18 |
| | Thermidor | Heat | Jul 19 – Aug 17 |
| | Fructidor | Fruit | Aug 18 – Sep 16 |

The **Sansculottides** (Sep 17–21) are dedicated to national celebrations: Virtue, Genius, Labour, Opinion, Rewards, and (in leap years) Revolution.

### The rural calendar

The most distinctive feature of the Republican Calendar is its **rural nomenclature**. The poet [Fabre d'Églantine](https://en.wikipedia.org/wiki/Fabre_d%27%C3%89glantine) replaced the Catholic saints' days with names drawn from the natural and agricultural world. Every single day of the 366-day cycle has a unique name, following a strict pattern:

- **Quintidi** (5th, 15th, 25th of each month): a domestic **animal** — horse, goose, pig, dog, bull, cow, etc.
- **Décadi** (10th, 20th, 30th of each month): an agricultural **tool** — plough, barrel, pickaxe, beehive, scythe, etc.
- **All other days**: a **plant**, flower, fruit, grain, or tree appropriate to the season.
- **Exception — Nivôse** (the deep winter month): non-animal, non-tool days are **minerals** and earths (peat, coal, sulfur, granite, iron, copper, etc.) instead of plants, since little grows in December–January.

This is what PyAlmanaque shows: the day's unique item, with a representative image and a link to learn more about it.

## How the app works

The request lifecycle for a single page load involves three steps: date conversion, translation, and image fetching.

### Step 1: Date conversion (`calendar_utils.py`)

The [convertdate](https://github.com/fitnr/convertdate) library handles the Gregorian-to-Republican conversion. Its `french_republican` module uses an equinox-based algorithm by default, computing the exact date of the autumn equinox each year to determine where Year N begins.

The `get_republican_date()` function calls `french_republican.from_gregorian()` to get the Republican `(year, month, day)` tuple, then enriches it with:

- **Décade day name**: computed as `JOURS_DECADE[(day - 1) % 10]`. The Sansculottides (month 13) have no décade, so this is `None` for those 5–6 days.
- **Month translation**: a lookup from a static dict (e.g., `"Vendémiaire"` → `"Month of the Grape Harvest"`).
- **Season**: determined by which group of three months the current month belongs to. Used for CSS theming.
- **Category**: the type of item for this day — `plant`, `animal`, `tool`, `mineral`, or `celebration`. Determined by the day's position within the décade and the month (Nivôse is the mineral exception). This drives the colored badge in the UI.
- **Thing of the day**: the French name of the item, retrieved via `french_republican.day_name(month, day)` from convertdate's built-in dataset of all 366 names.

The function returns a dict with all of this, plus the formatted Republican date string (e.g., `"11 Ventôse 234"`).

### Step 2: Translation (`translations.py`)

The convertdate library provides the French names, but the app needs English names for display and for Wikipedia lookups. The `translations.py` file contains a manually curated dictionary mapping all 366 French day names to a tuple of `(english_display_name, wikipedia_article_title)`:

```python
"Cornouiller": ("Dogwood", "Cornus"),
"Mouron": ("Scarlet pimpernel", "Lysimachia arvensis"),
"Hoyau": ("Mattock", "Mattock"),
```

The two values in each tuple serve different purposes:
- **Display name**: shown to the user as the English translation (e.g., "Dogwood").
- **Wikipedia article title**: the exact title of the English Wikipedia article used for both the image fetch and the link. This often differs from the common name — *Cornouiller* is commonly "Dogwood", but the Wikipedia article with the best image is [Cornus](https://en.wikipedia.org/wiki/Cornus).

This separation was necessary because:
1. Many common English names resolve to disambiguation pages on Wikipedia (e.g., "Orange" → the city, not the fruit).
2. Some Wikipedia articles lack a main image, while a related article (often the Latin genus name) has one.
3. Two different French items might map to the same English name (e.g., both *Chamerisier* and *Chèvrefeuille* translate to "Honeysuckle"), so they need distinct Wikipedia articles to get distinct images.

All 366 entries have been verified to produce a unique image. The verification scripts (`verify_images.py` and `verify_duplicates.py`) use Wikipedia's batch query API (up to 50 titles per request) to check every day in a few seconds.

### Step 3: Image fetching (`app.py`)

The `get_thing_info()` function takes the French day name, looks up its translation, and fetches a thumbnail image from Wikipedia.

The image lookup uses the [MediaWiki `pageimages` API](https://www.mediawiki.org/wiki/API:Pageimages):

```
GET https://en.wikipedia.org/w/api.php
  ?action=query
  &titles=Cornus
  &prop=pageimages
  &pithumbsize=400
  &format=json
```

This returns a JSON response containing the URL of the article's main image, scaled to 400px width. The `pithumbsize` parameter triggers Wikimedia's on-the-fly thumbnail generation.

The fallback chain is:
1. **English Wikipedia** using the `wikipedia_article` from `translations.py`
2. **French Wikipedia** using the original French name (for the ~24 items where English Wikipedia has no image but French Wikipedia does)

Results are cached in an in-memory dict (`_image_cache`) keyed by `"{lang}:{title}"`. Since the calendar only has 366 unique items and the app rarely restarts in production, this means at most 366 API calls over the lifetime of the process. Subsequent requests for the same day are served instantly from cache.

The `<img>` tag in the template uses `referrerpolicy="no-referrer"` to prevent Wikimedia's hotlink protection from blocking the thumbnails.

### Security hardening

The Flask app now sends a restrictive set of response headers on every page:

- `Content-Security-Policy` limits resources to the local app and HTTPS-hosted Wikimedia images.
- `X-Frame-Options: DENY` and `Cross-Origin-Opener-Policy: same-origin` reduce clickjacking and window-opener risks.
- `X-Content-Type-Options: nosniff`, `Referrer-Policy`, and `Permissions-Policy` disable unnecessary browser features and tighten default behavior.
- `Strict-Transport-Security` is added automatically on HTTPS requests so browsers keep using TLS after the first secure visit.

Wikipedia thumbnail URLs are also validated before rendering, and only `https://*.wikimedia.org` images are accepted.

These hardening steps improve the app's security posture, but they do not automatically clear a Chrome Safe Browsing warning on a shared `*.azurewebsites.net` hostname. If the deployed site is still flagged, check the domain in the [Google Transparency Report](https://transparencyreport.google.com/safe-browsing/search?hl=en), request a review after remediation, and consider moving the app to a custom domain with its own reputation history.

### The template (`templates/index.html`)

The single Jinja2 template renders all the data into a centered, single-column layout. Key details:

- The `<body>` tag gets a CSS class like `season-winter` or `season-spring`, which the stylesheet uses to apply season-specific background gradients and text colors.
- The French article prefix (*du*, *de l'*, *de la*) before the day name is computed inline using a Jinja2 conditional that checks if the first character is a vowel.
- The category badge (*plant*, *animal*, *tool*, *mineral*, *celebration*) gets a colored pill via CSS classes like `.badge-plant`, `.badge-animal`, etc.
- Navigation arrows (`&larr;` / `&rarr;`) link to `?date=YYYY-MM-DD` for the previous and next Gregorian days. A "Today" button appears only when viewing a date other than today.

### Visual theming (`static/style.css`)

The page has no JavaScript. All interactivity comes from server-rendered HTML and CSS transitions. The design uses Georgia serif for a period-appropriate feel.

Five season themes are defined, each setting a diagonal gradient background and a matching text color:

| Season | Background | Text |
|--------|-----------|------|
| Autumn | Warm orange `#f5e6d0` → `#e8c9a0` | Dark brown `#4a3520` |
| Winter | Cool blue `#dce8f0` → `#b8cfe0` | Dark slate `#2a3a4a` |
| Spring | Soft green `#e0f0d8` → `#c8e0b0` | Dark green `#2a4020` |
| Summer | Warm gold `#f5f0d0` → `#e8d888` | Dark olive `#4a4020` |
| Special | Lavender `#dce0f5` → `#c0c8e8` | Dark indigo `#2a2a4a` |

The "special" theme is used for the Sansculottides complementary days.

Category badges use distinct background colors: green for plants, brown for animals, gray for tools, slate for minerals, and burgundy for celebrations.

## Project structure

```
pyalmanaque/
├── app.py               # Flask application: single route, Wikipedia API, image caching
├── calendar_utils.py    # Date conversion, décade names, season/category classification
├── translations.py      # All 366 French→English mappings with Wikipedia article titles
├── templates/
│   └── index.html       # Jinja2 template: season-themed layout, navigation, image display
├── static/
│   └── style.css        # CSS: season gradients, responsive layout, category badges
├── pyproject.toml       # PEP 621 project metadata and dependencies
├── uv.lock              # Locked dependency versions
├── Dockerfile           # Container image for production deployment
├── mise.toml            # Task runner: dev server, Azure deployment pipeline
├── render.yaml          # Alternative Render.com deployment config
├── .gitignore           # Excludes .venv, .azure, __pycache__, test/verify scripts
└── .dockerignore        # Excludes .venv, __pycache__, test/verify scripts from image
```

## Running locally

```bash
uv sync
mise run dev
# or: uv run flask --app app run
```

Open http://127.0.0.1:5000. Navigate to any date with `?date=YYYY-MM-DD`.

## Deployment to Azure

The app is deployed to **Azure App Service** (Linux, Free F1 tier) in the **West Europe** region. The deployment pipeline is defined in `mise.toml` as a chain of dependent tasks.

### What `mise run deploy` does

Running `mise run deploy` executes the following steps in order:

#### 1. `azure:login` — Authenticate with Azure

```bash
az login
```

Opens a browser for interactive OAuth login. This creates a session token stored locally by the Azure CLI. Subsequent `az` commands use this token. The session expires after 90 days of inactivity.

#### 2. `azure:group` — Create the resource group

```bash
az group create --name pyalmanaque-rg --location westeurope
```

A [resource group](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/overview#resource-groups) is Azure's logical container for related resources. All resources for this app (the App Service plan and the web app) live in `pyalmanaque-rg`. The `westeurope` location (Amsterdam) was chosen for proximity to France. This command is idempotent — it succeeds silently if the group already exists.

#### 3. `azure:upload` — Deploy the application

```bash
az webapp up --name pyalmanaque --resource-group pyalmanaque-rg \
  --runtime 'PYTHON:3.13' --sku F1 --location westeurope
```

[`az webapp up`](https://learn.microsoft.com/en-us/cli/azure/webapp?view=azure-cli-latest#az-webapp-up) is a high-level command that does several things in one step:

1. **Creates an App Service plan** (if it doesn't exist) — the compute resource that hosts the app. The `F1` SKU is the free tier (60 CPU-minutes/day, 1 GB RAM, no custom domain, no SSL).
2. **Creates the web app** (if it doesn't exist) — a Linux container running Python 3.13 on the App Service plan.
3. **Zips the current directory** and uploads it to the app via the Kudu deployment engine. Kudu detects `pyproject.toml`, runs `pip install`, and stages the app.
4. **Starts the app** with Azure's default Python startup, which runs Oryx build detection.

This command is also idempotent — on subsequent runs, it updates the existing app instead of creating a new one.

#### 4. `azure:configure` — Set the startup command

```bash
az webapp config set --name pyalmanaque --resource-group pyalmanaque-rg \
  --startup-file 'gunicorn --bind 0.0.0.0:8000 app:app'
```

By default, Azure's Python runtime tries to auto-detect the web framework and start the app. This override ensures [gunicorn](https://gunicorn.org/) is used as the WSGI server, binding to port 8000 (Azure's internal port for Linux App Service). Gunicorn handles concurrent requests, worker management, and graceful restarts — essential for production but unnecessary for local development where Flask's built-in server suffices.

The `app:app` argument tells gunicorn to import the `app` Flask object from the `app` module (i.e., `app.py`).

### Alternative: Docker deployment

The repository also includes a `Dockerfile` for container-based deployment (used by the `render.yaml` config for Render.com, or usable with any container platform):

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
ENV PORT=10000
EXPOSE ${PORT}
CMD uv run gunicorn --bind 0.0.0.0:${PORT} app:app
```

This uses a multi-stage copy of [uv](https://github.com/astral-sh/uv) from its official Docker image, installs dependencies from the lockfile, and runs gunicorn on the port specified by the `PORT` environment variable (which hosting platforms like Render set automatically).

## Dependencies

| Package | Purpose |
|---------|---------|
| [Flask](https://flask.palletsprojects.com/) | Web framework: routing, Jinja2 templates, static file serving |
| [convertdate](https://convertdate.readthedocs.io/) | Gregorian ↔ French Republican calendar conversion, including all 366 day names |
| [requests](https://requests.readthedocs.io/) | HTTP client for the Wikipedia `pageimages` API |
| [gunicorn](https://gunicorn.org/) | Production WSGI server (used in Azure/Docker, not needed locally) |
