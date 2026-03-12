# Shared Pendulum Module

Common pendulum construction logic shared by all pendulum wave variants. Each variant computes its own layout (list of `PendulumSpec`) and calls `create_pendulums()` to build the VElements.

## Modules

- `pendulum.py`: `PendulumSpec` dataclass, bob/arm interpolation functions, `create_pendulums()` factory
- `physics.py`: pendulum cycle precomputation and lookup
