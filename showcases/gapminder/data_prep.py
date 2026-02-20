"""Data preparation for Gapminder bubble chart.

Loads CSV, filters to top N countries by population, and returns
raw data points per actual CSV year for svan2d keystate interpolation.
"""

import pandas as pd
from dataclasses import dataclass


# Default column mapping from gapminder CSV to internal names
DEFAULT_COLUMN_MAP = {
    "lifeExp": "life_exp",
    "gdpPercap": "gdp_per_cap",
    "pop": "population",
}


@dataclass
class CountryDataPoint:
    """Single data point for a country at a specific interpolated time."""

    country: str
    continent: str
    year: float
    life_exp: float
    gdp_per_cap: float
    population: float


def get_country_data(
    data_path: str,
    top_n: int = 40,
    column_map: dict[str, str] | None = None,
) -> dict[str, list[CountryDataPoint]]:
    """Load and preprocess gapminder data.

    Args:
        data_path: Path to CSV file with gapminder-format data
        top_n: Number of countries to include (by max population)
        column_map: Column rename mapping (CSV name → internal name).
                    Defaults to gapminder standard columns.

    Returns:
        Dictionary mapping country names to list of CountryDataPoint objects
    """
    df = pd.read_csv(data_path)

    # Rename columns to internal names
    rename_map = column_map or DEFAULT_COLUMN_MAP
    df = df.rename(columns=rename_map)

    required = ["country", "continent", "year", "life_exp", "gdp_per_cap", "population"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Select top_n countries by max population across all years
    max_pop = df.groupby("country")["population"].max()
    top_countries = max_pop.nlargest(top_n).index.tolist()
    df_filtered = df[df["country"].isin(top_countries)].copy()

    print(f"Filtered to {len(top_countries)} countries by max population")

    # Build per-country data points from raw CSV rows
    result: dict[str, list[CountryDataPoint]] = {}

    for country_name, group in df_filtered.groupby("country"):
        name = str(country_name)
        group = group.sort_values("year")
        continent = group["continent"].iloc[0]
        points = []
        for _, row in group.iterrows():
            points.append(
                CountryDataPoint(
                    country=name,
                    continent=continent,
                    year=float(row["year"]),
                    life_exp=float(row["life_exp"]),
                    gdp_per_cap=max(1.0, float(row["gdp_per_cap"])),
                    population=max(0.0, float(row["population"])),
                )
            )
        result[name] = points

    return result
