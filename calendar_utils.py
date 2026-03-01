from datetime import date

from convertdate import french_republican

JOURS_DECADE = [
    "Primidi", "Duodi", "Tridi", "Quartidi", "Quintidi",
    "Sextidi", "Septidi", "Octidi", "Nonidi", "Décadi",
]

MONTH_TRANSLATIONS = {
    "Vendémiaire": "Month of the Grape Harvest",
    "Brumaire": "Month of Fog",
    "Frimaire": "Month of Frost",
    "Nivôse": "Month of Snow",
    "Pluviôse": "Month of Rain",
    "Ventôse": "Month of Wind",
    "Germinal": "Month of Germination",
    "Floréal": "Month of Flowers",
    "Prairial": "Month of Meadows",
    "Messidor": "Month of Harvest",
    "Thermidor": "Month of Heat",
    "Fructidor": "Month of Fruit",
    "Sansculottides": "Complementary Days",
}

SEASONS = {
    "autumn": ["Vendémiaire", "Brumaire", "Frimaire"],
    "winter": ["Nivôse", "Pluviôse", "Ventôse"],
    "spring": ["Germinal", "Floréal", "Prairial"],
    "summer": ["Messidor", "Thermidor", "Fructidor"],
}


def day_category(month: int, day: int) -> str:
    """Return the category for a given day.

    Rules from Fabre d'Églantine:
    - Days ending in 0 (décadi): agricultural tool
    - Days ending in 5 (quintidi): domestic animal
    - Nivôse non-tool/non-animal days: mineral
    - All other days: plant
    - Sansculottides: celebration
    """
    if month == 13:
        return "celebration"
    if day % 10 == 0:
        return "tool"
    if day % 10 == 5:
        return "animal"
    month_name = french_republican.MONTHS[month - 1]
    if month_name == "Nivôse":
        return "mineral"
    return "plant"


def get_republican_date(gregorian_date: date | None = None) -> dict:
    """Convert a Gregorian date to a rich Republican calendar dict."""
    if gregorian_date is None:
        gregorian_date = date.today()

    year, month, day = french_republican.from_gregorian(
        gregorian_date.year, gregorian_date.month, gregorian_date.day
    )

    month_name = french_republican.MONTHS[month - 1]
    thing_of_day = french_republican.day_name(month, day)

    if month <= 12:
        decade_day_index = (day - 1) % 10
        decade_day_name = JOURS_DECADE[decade_day_index]
    else:
        decade_day_name = None

    season = "special"
    for s, months in SEASONS.items():
        if month_name in months:
            season = s
            break

    category = day_category(month, day)

    return {
        "year": year,
        "month": month,
        "month_name": month_name,
        "month_translation": MONTH_TRANSLATIONS.get(month_name, ""),
        "day": day,
        "decade_day_name": decade_day_name,
        "thing_of_day": thing_of_day,
        "category": category,
        "season": season,
        "formatted": french_republican.format(year, month, day),
        "gregorian_date": gregorian_date,
    }
