import pandas as pd
from enum import Enum
from dataclasses import dataclass
from scipy.interpolate import PchipInterpolator, interp1d


class InterpolationMethod(Enum):
    LINEAR = "linear"
    PCHIP = "pchip"


@dataclass
class CompanyDataPoint:
    """Single data point for a company at a specific time."""

    name: str
    category: str
    year: float
    value: float
    rank: int
    ratio_of_top: float


def get_company_data(
    data_path: str,
    top_n: int = 10,
    interpolated_data_per_year: int = 10,
    interpolation_method: InterpolationMethod = InterpolationMethod.PCHIP,
    fill_value: float = 0.0,
) -> dict[str, list[CompanyDataPoint]]:
    """
    Load and preprocess company data with interpolation.

    Args:
        data_path: Path to CSV file
        top_n: Number of top companies to include
        interpolated_data_per_year: Number of interpolated points between years
        interpolation_method: LINEAR or PCHIP interpolation
        fill_value: Value to use for missing timepoints (default 0.0)

    Returns:
        Dictionary mapping company names to list of CompanyDataPoint objects
    """
    # Load and prepare data
    df = pd.read_csv(data_path, parse_dates=["date"])
    df["year"] = df["date"].dt.year  # type: ignore[union-attr]
    df = df[["name", "category", "value", "year"]]

    # Add ranks
    df["rank"] = (
        df.groupby("year")["value"].rank(method="dense", ascending=False).astype(int)
    )

    # Filter to companies which at least are in the "top_n"
    top_names = df[df["rank"] <= top_n]["name"].unique()
    df_filtered = df[df["name"].isin(top_names)].copy()

    print(f"Filtered to {len(top_names)} companies that appeared in top {top_n}")

    # Get all timepoints that will exist after interpolation
    all_years = sorted(df_filtered["year"].unique())
    all_timepoints = []

    for i in range(len(all_years) - 1):
        year_a = all_years[i]
        year_b = all_years[i + 1]
        for j in range(interpolated_data_per_year + 1):
            t = j / (interpolated_data_per_year + 1)
            all_timepoints.append(year_a * (1 - t) + year_b * t)
    all_timepoints.append(float(all_years[-1]))

    # Create interpolators for each company
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

        # Get interpolated values for all companies at this timepoint
        for name, info in company_info.items():
            min_year, max_year = info["year_range"]

            if min_year <= timepoint <= max_year:
                value = float(info["interpolator"](timepoint))
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

        # Create CompanyDataPoint for each company at this timepoint
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
