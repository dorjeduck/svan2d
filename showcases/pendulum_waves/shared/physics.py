"""Shared pendulum physics for all pendulum wave variants."""

import math


def precompute_pendulum_cycle(
    max_angle_rad: float, samples: int = 512
) -> list[float]:
    """Precompute one exact pendulum cycle using RK4 integration.

    Solves theta'' = -sin(theta) starting from theta=0 (bottom, max velocity).
    Returns `samples + 1` angle values evenly spaced over one period.
    """
    omega_max = math.sqrt(2.0 * (1.0 - math.cos(max_angle_rad)))

    def _rk4_step(theta: float, omega: float, dt: float):
        k1_t, k1_o = omega, -math.sin(theta)
        k2_t, k2_o = omega + dt / 2 * k1_o, -math.sin(theta + dt / 2 * k1_t)
        k3_t, k3_o = omega + dt / 2 * k2_o, -math.sin(theta + dt / 2 * k2_t)
        k4_t, k4_o = omega + dt * k3_o, -math.sin(theta + dt * k3_t)
        new_theta = theta + dt / 6 * (k1_t + 2 * k2_t + 2 * k3_t + k4_t)
        new_omega = omega + dt / 6 * (k1_o + 2 * k2_o + 2 * k3_o + k4_o)
        return new_theta, new_omega

    dt_fine = 0.0001
    theta, omega = 0.0, omega_max
    quarter_time = 0.0
    while omega > 0:
        theta, omega = _rk4_step(theta, omega, dt_fine)
        quarter_time += dt_fine
    period = 4.0 * quarter_time

    dt = period / samples
    theta, omega = 0.0, omega_max
    angles = [theta]
    for _ in range(samples):
        theta, omega = _rk4_step(theta, omega, dt)
        angles.append(theta)

    return angles


def lookup_cycle(cycle: list[float], phase: float) -> float:
    """Linearly interpolate into the precomputed cycle table."""
    phase = phase % 1.0
    idx = phase * (len(cycle) - 1)
    i = int(idx)
    frac = idx - i
    if i >= len(cycle) - 1:
        return cycle[-1]
    return cycle[i] + frac * (cycle[i + 1] - cycle[i])
