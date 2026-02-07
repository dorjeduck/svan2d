import pandas as pd
from enum import Enum
from dataclasses import dataclass
from scipy.interpolate import PchipInterpolator, interp1d


class InterpolationMethod(Enum):
    LINEAR = "linear"
    PCHIP = "pchip"


@dataclass
class CompanyDataPoint:
    """Single data point for a country at a specific time."""

    name: str
    category: str
    year: float
    value: float
    rank: int
    ratio_of_top: float


# Map countries to geographic regions for color grouping
REGION_MAP = {
    # Asia
    "China": "Asia",
    "India": "Asia",
    "Japan": "Asia",
    "Korea": "Asia",
    "Indonesia": "Asia",
    "Thailand": "Asia",
    # Europe
    "Germany": "Europe",
    "France": "Europe",
    "United Kingdom": "Europe",
    "Netherlands": "Europe",
    "Belgium": "Europe",
    "Sweden": "Europe",
    "Norway": "Europe",
    "Italy": "Europe",
    "Spain": "Europe",
    "Denmark": "Europe",
    "Finland": "Europe",
    "Austria": "Europe",
    "Switzerland": "Europe",
    "Portugal": "Europe",
    "Ireland": "Europe",
    "Poland": "Europe",
    "Iceland": "Europe",
    "Greece": "Europe",
    "Czech Republic": "Europe",
    "Hungary": "Europe",
    "Romania": "Europe",
    "Croatia": "Europe",
    "Bulgaria": "Europe",
    "Slovakia": "Europe",
    "Slovenia": "Europe",
    "Lithuania": "Europe",
    "Latvia": "Europe",
    "Estonia": "Europe",
    "Luxembourg": "Europe",
    "Cyprus": "Europe",
    "Turkiye": "Europe",
    # North America
    "USA": "North America",
    "Canada": "North America",
    "Mexico": "North America",
    "Costa Rica": "North America",
    # South America
    "Brazil": "South America",
    "Chile": "South America",
    "Colombia": "South America",
    # Oceania
    "Australia": "Oceania",
    "New Zealand": "Oceania",
    # Middle East & Africa
    "Israel": "Middle East & Africa",
    "United Arab Emirates": "Middle East & Africa",
    "South Africa": "Middle East & Africa",
    "Seychelles": "Middle East & Africa",
}

# Aggregate regions to exclude
EXCLUDE_REGIONS = {"World", "EU27", "Europe", "Rest of the world"}


def get_company_data(
    data_path: str,
    top_n: int = 10,
    interpolated_data_per_year: int = 10,
    interpolation_method: InterpolationMethod = InterpolationMethod.PCHIP,
    fill_value: float = 0.0,
) -> dict[str, list[CompanyDataPoint]]:
    """
    Load and preprocess EV sales data with interpolation.

    Filters for historical car EV sales (BEV + PHEV combined),
    excludes aggregate regions, and assigns geographic categories.

    Args:
        data_path: Path to IEA Global EV Data CSV
        top_n: Number of top countries to include
        interpolated_data_per_year: Number of interpolated points between years
        interpolation_method: LINEAR or PCHIP interpolation
        fill_value: Value to use for missing timepoints (default 0.0)

    Returns:
        Dictionary mapping country names to list of CompanyDataPoint objects
    """
    df = pd.read_csv(data_path)

    # Filter: historical, car EV sales, BEV + PHEV only
    mask = (
        (df["category"] == "Historical")
        & (df["parameter"] == "EV sales")
        & (df["powertrain"].isin(["BEV", "PHEV"]))
        & (df["mode"] == "Cars")
        & (~df["region"].isin(EXCLUDE_REGIONS))
    )
    df = df[mask].copy()

    # Sum BEV + PHEV per region per year
    df = df.groupby(["region", "year"])["value"].sum().reset_index()
    df.rename(columns={"region": "name"}, inplace=True)

    # Assign geographic category
    df["category"] = df["name"].map(REGION_MAP).fillna("Other")

    # Add ranks per year
    df["rank"] = (
        df.groupby("year")["value"].rank(method="dense", ascending=False).astype(int)
    )

    # Filter to countries that appeared in top_n at least once
    top_names = df[df["rank"] <= top_n]["name"].unique()
    df_filtered = df[df["name"].isin(top_names)].copy()

    print(f"Filtered to {len(top_names)} countries that appeared in top {top_n}")

    # Get all timepoints after interpolation
    all_years = sorted(df_filtered["year"].unique())
    all_timepoints = []

    for i in range(len(all_years) - 1):
        year_a = all_years[i]
        year_b = all_years[i + 1]
        for j in range(interpolated_data_per_year + 1):
            t = j / (interpolated_data_per_year + 1)
            all_timepoints.append(year_a * (1 - t) + year_b * t)
    all_timepoints.append(float(all_years[-1]))

    # Create interpolators for each country
    company_info = {}

    for name, group in df_filtered.groupby("name"):
        group = group.sort_values("year")
        xs = group["year"].to_numpy()
        ys = group["value"].to_numpy()

        year_range = (float(xs.min()), float(xs.max()))
        category = group["category"].iloc[0]

        if interpolation_method == InterpolationMethod.PCHIP:
            interpolator = PchipInterpolator(xs, ys)
        else:
            interpolator = interp1d(xs, ys, kind="linear")

        company_info[name] = {
            "category": category,
            "interpolator": interpolator,
            "year_range": year_range,
        }

    # Initialize result dictionary
    result = {name: [] for name in company_info.keys()}

    # Build data points for each timepoint
    for timepoint in all_timepoints:
        frame_values = {}

        for name, info in company_info.items():
            min_year, max_year = info["year_range"]

            if min_year <= timepoint <= max_year:
                value = max(0, float(info["interpolator"](timepoint)))
            else:
                value = fill_value

            frame_values[name] = value

        # Calculate ranks and ratios for this timepoint
        max_value = max(frame_values.values())
        sorted_names = sorted(
            frame_values.keys(), key=lambda n: frame_values[n], reverse=True
        )

        ranks = {}
        current_rank = 1
        prev_value = None

        for name in sorted_names:
            if frame_values[name] != prev_value:
                ranks[name] = current_rank
                prev_value = frame_values[name]
            else:
                ranks[name] = current_rank
            current_rank += 1

        for name, info in company_info.items():
            value = frame_values[name]
            rank = ranks[name]
            ratio = (value / max_value) if max_value > 0 else 0.0

            result[name].append(
                CompanyDataPoint(
                    name=name,
                    category=info["category"],
                    year=timepoint,
                    value=value,
                    rank=rank,
                    ratio_of_top=ratio,
                )
            )

    return result
