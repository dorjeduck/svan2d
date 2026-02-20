"""Coordinate mapping for Gapminder plot area.

Maps GDP per capita (log scale) to X and life expectancy (linear) to Y
within a centered-origin plot area.
"""

import math
from dataclasses import dataclass


@dataclass
class PlotConfig:
    """Configuration for plot area bounds and axis ranges."""

    # Plot area bounds (centered origin)
    plot_left: float = -425.0
    plot_right: float = 460.0
    plot_top: float = -250.0
    plot_bottom: float = 225.0

    # GDP log scale range
    gdp_min: float = 200.0
    gdp_max: float = 120000.0

    # Life expectancy linear range
    life_exp_min: float = 20.0
    life_exp_max: float = 90.0

    @property
    def plot_width(self) -> float:
        return self.plot_right - self.plot_left

    @property
    def plot_height(self) -> float:
        return self.plot_bottom - self.plot_top


def gdp_to_x(gdp: float, config: PlotConfig) -> float:
    """Map GDP per capita to X coordinate using log10 scale."""
    log_min = math.log10(config.gdp_min)
    log_max = math.log10(config.gdp_max)
    log_gdp = math.log10(max(config.gdp_min, gdp))
    t = (log_gdp - log_min) / (log_max - log_min)
    return config.plot_left + t * config.plot_width


def life_exp_to_y(life_exp: float, config: PlotConfig) -> float:
    """Map life expectancy to Y coordinate (higher life exp = up = lower Y in center origin)."""
    t = (life_exp - config.life_exp_min) / (config.life_exp_max - config.life_exp_min)
    return config.plot_bottom - t * config.plot_height
