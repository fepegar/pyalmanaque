from datetime import date, timedelta
from urllib.parse import quote

import requests
from flask import Flask, render_template, request

from calendar_utils import get_republican_date
from translations import get_translation

app = Flask(__name__)

_image_cache: dict[str, dict | None] = {}

_HEADERS = {"User-Agent": "PyAlmanaque/0.1 (educational project)"}


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
                thumbnail_url = page_data.get("thumbnail", {}).get("source")
    except (requests.RequestException, KeyError, ValueError):
        pass

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


def main():
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    main()
