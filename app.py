from datetime import date, timedelta
from urllib.parse import quote, urlparse

import requests
from flask import Flask, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

from calendar_utils import get_republican_date
from translations import get_translation

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)

_image_cache: dict[str, str | None] = {}

_HEADERS = {"User-Agent": "PyAlmanaque/0.1 (educational project)"}
_CSP = (
    "default-src 'self'; "
    "img-src 'self' https://*.wikimedia.org data:; "
    "style-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)


def is_allowed_thumbnail_url(url: str) -> bool:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    return parsed.scheme == "https" and (
        hostname == "wikimedia.org" or hostname.endswith(".wikimedia.org")
    )


def fetch_wikipedia_image(title: str, lang: str = "en", size: int = 400) -> str | None:
    """Fetch the thumbnail URL from Wikipedia for a given article title."""
    cache_key = f"{lang}:{title}"
    if cache_key in _image_cache:
        return _image_cache[cache_key]

    api_url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": title,
        "prop": "pageimages",
        "pithumbsize": size,
        "format": "json",
    }

    thumbnail_url = None
    try:
        resp = requests.get(api_url, params=params, timeout=5, headers=_HEADERS)
        resp.raise_for_status()
        pages = resp.json().get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if page_id != "-1":
                candidate_url = page_data.get("thumbnail", {}).get("source")
                if candidate_url and is_allowed_thumbnail_url(candidate_url):
                    thumbnail_url = candidate_url
                    break
                if candidate_url:
                    app.logger.warning(
                        "Rejected non-Wikimedia thumbnail URL for %s (%s): %s",
                        title,
                        lang,
                        candidate_url,
                    )
    except requests.RequestException as exc:
        app.logger.warning(
            "Failed to fetch Wikipedia image for %s (%s): %s",
            title,
            lang,
            exc,
        )
    except ValueError as exc:
        app.logger.warning(
            "Failed to decode Wikipedia image response for %s (%s): %s",
            title,
            lang,
            exc,
        )

    _image_cache[cache_key] = thumbnail_url
    return thumbnail_url


def get_thing_info(french_name: str) -> dict:
    """Get English name, image, and Wikipedia URL for a day's thing."""
    en_name, wiki_article = get_translation(french_name)
    page_url = f"https://en.wikipedia.org/wiki/{quote(wiki_article)}"

    # Try English Wikipedia first, then French
    thumbnail = fetch_wikipedia_image(wiki_article, lang="en")
    if not thumbnail:
        thumbnail = fetch_wikipedia_image(french_name, lang="fr")

    return {
        "en_name": en_name,
        "thumbnail_url": thumbnail,
        "page_url": page_url,
    }


@app.route("/")
def index():
    date_str = request.args.get("date")
    if date_str:
        try:
            gregorian = date.fromisoformat(date_str)
        except ValueError:
            gregorian = date.today()
    else:
        gregorian = date.today()

    rep_date = get_republican_date(gregorian)
    image_info = get_thing_info(rep_date["thing_of_day"])

    prev_date = (gregorian - timedelta(days=1)).isoformat()
    next_date = (gregorian + timedelta(days=1)).isoformat()
    is_today = gregorian == date.today()

    return render_template(
        "index.html", rep=rep_date, image=image_info,
        prev_date=prev_date, next_date=next_date, is_today=is_today,
    )


@app.after_request
def add_security_headers(response):
    response.headers["Content-Security-Policy"] = _CSP
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = (
        "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
        "microphone=(), payment=(), usb=()"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    if request.is_secure:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response


def main():
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    main()
