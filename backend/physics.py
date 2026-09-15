"""
Physics simulation module for 2D Projectile Motion.
Computes Ideal, Euler numerical integration, and Runge-Kutta 4th Order (RK4) trajectories
accounting for aerodynamic drag, wind velocity, and gravity.
"""

from typing import Dict, Any, List
import math


def _calculate_derivatives(vx: float, vy: float, mass: float, k: float, wind_x: float, g: float):
    """
    Computes accelerations ax and ay given current velocity, mass, drag factor, and wind.
    """
    v_rel_x = vx - wind_x
    v_rel = math.sqrt(v_rel_x**2 + vy**2)
    drag_factor = (k / mass) * v_rel if mass > 0 else 0.0

    ax = -drag_factor * v_rel_x
    ay = -g - drag_factor * vy
    return ax, ay


def _create_point_dict(t: float, x: float, y: float, vx: float, vy: float, mass: float, g: float) -> Dict[str, float]:
    """
    Helper to create point record with position, velocity, and energies.
    """
    clamped_y = max(0.0, y)
    v_sq = vx**2 + vy**2
    ek = 0.5 * mass * v_sq
    ep = mass * g * clamped_y
    em = ek + ep

    return {
        "time": round(t, 4),
        "x": round(x, 4),
        "y": round(clamped_y, 4),
        "vx": round(vx, 4),
        "vy": round(vy, 4),
        "Ek": round(ek, 4),
        "Ep": round(ep, 4),
        "Em": round(em, 4),
    }


def _interpolate_landing(
    t_prev: float, x_prev: float, y_prev: float, vx_prev: float, vy_prev: float,
    t_curr: float, x_curr: float, y_curr: float, vx_curr: float, vy_curr: float,
    mass: float, g: float
) -> Dict[str, float]:
    """
    Linearly interpolates state when y drops below 0 to find exact ground impact point (y=0).
    """
    if y_curr == y_prev:
        frac = 0.0
    else:
        frac = (0.0 - y_prev) / (y_curr - y_prev)
    frac = max(0.0, min(1.0, frac))

    t_land = t_prev + frac * (t_curr - t_prev)
    x_land = x_prev + frac * (x_curr - x_prev)
    y_land = 0.0
    vx_land = vx_prev + frac * (vx_curr - vx_prev)
    vy_land = vy_prev + frac * (vy_curr - vy_prev)

    return _create_point_dict(t_land, x_land, y_land, vx_land, vy_land, mass, g)


def _compute_summary(points: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Calculates max height, max range, flight time, and impact velocity from points.
    """
    if not points:
        return {"max_height": 0.0, "max_range": 0.0, "flight_time": 0.0, "impact_velocity": 0.0}

    max_height = max(p["y"] for p in points)
    last_point = points[-1]
    flight_time = last_point["time"]
    max_range = last_point["x"]
    impact_velocity = math.sqrt(last_point["vx"]**2 + last_point["vy"]**2)

    return {
        "max_height": round(max_height, 4),
        "max_range": round(max_range, 4),
        "flight_time": round(flight_time, 4),
        "impact_velocity": round(impact_velocity, 4),
    }


def _simulate_ideal(v0: float, angle_rad: float, mass: float, g: float, dt: float, max_steps: int = 100_000):
    """
    Analytical trajectory with no air resistance or wind.
    """
    vx0 = v0 * math.cos(angle_rad)
    vy0 = v0 * math.sin(angle_rad)

    points: List[Dict[str, float]] = []

    if vy0 < 0 or g <= 0:
        # Fired downward or zero gravity corner case
        points.append(_create_point_dict(0.0, 0.0, 0.0, vx0, vy0, mass, g))
        return {"summary": _compute_summary(points), "points": points}

    t_flight = (2.0 * vy0) / g if g > 0 else 0.0

    t = 0.0
    step = 0
    while t < t_flight and step < max_steps:
        x = vx0 * t
        y = vy0 * t - 0.5 * g * (t**2)
        vx = vx0
        vy = vy0 - g * t

        points.append(_create_point_dict(t, x, y, vx, vy, mass, g))
        t += dt
        step += 1

    # Final impact point at t = t_flight
    x_final = vx0 * t_flight
    y_final = 0.0
    vx_final = vx0
    vy_final = vy0 - g * t_flight
    points.append(_create_point_dict(t_flight, x_final, y_final, vx_final, vy_final, mass, g))

    return {
        "summary": _compute_summary(points),
        "points": points,
    }


def _simulate_euler(v0: float, angle_rad: float, mass: float, k: float, wind_x: float, g: float, dt: float, max_steps: int = 100_000):
    """
    Numerical trajectory using Euler's integration method under drag and wind.
    """
    t = 0.0
    x = 0.0
    y = 0.0
    vx = v0 * math.cos(angle_rad)
    vy = v0 * math.sin(angle_rad)

    points: List[Dict[str, float]] = [_create_point_dict(t, x, y, vx, vy, mass, g)]

    for _ in range(max_steps):
        ax, ay = _calculate_derivatives(vx, vy, mass, k, wind_x, g)

        x_next = x + vx * dt
        y_next = y + vy * dt
        vx_next = vx + ax * dt
        vy_next = vy + ay * dt
        t_next = t + dt

        if y_next < 0.0:
            landing_point = _interpolate_landing(
                t, x, y, vx, vy,
                t_next, x_next, y_next, vx_next, vy_next,
                mass, g
            )
            points.append(landing_point)
            break

        points.append(_create_point_dict(t_next, x_next, y_next, vx_next, vy_next, mass, g))

        t, x, y, vx, vy = t_next, x_next, y_next, vx_next, vy_next

    return {
        "summary": _compute_summary(points),
        "points": points,
    }


def _simulate_rk4(v0: float, angle_rad: float, mass: float, k: float, wind_x: float, g: float, dt: float, max_steps: int = 100_000):
    """
    Numerical trajectory using 4th Order Runge-Kutta (RK4) integration under drag and wind.
    State vector: [x, y, vx, vy]
    """
    t = 0.0
    x = 0.0
    y = 0.0
    vx = v0 * math.cos(angle_rad)
    vy = v0 * math.sin(angle_rad)

    points: List[Dict[str, float]] = [_create_point_dict(t, x, y, vx, vy, mass, g)]

    def derivatives(state):
        _x, _y, _vx, _vy = state
        ax, ay = _calculate_derivatives(_vx, _vy, mass, k, wind_x, g)
        return [_vx, _vy, ax, ay]

    state = [x, y, vx, vy]

    for _ in range(max_steps):
        # RK4 steps
        k1 = derivatives(state)

        state_k2 = [s + 0.5 * dt * d for s, d in zip(state, k1)]
        k2 = derivatives(state_k2)

        state_k3 = [s + 0.5 * dt * d for s, d in zip(state, k2)]
        k3 = derivatives(state_k3)

        state_k4 = [s + dt * d for s, d in zip(state, k3)]
        k4 = derivatives(state_k4)

        next_state = [
            s + (dt / 6.0) * (d1 + 2.0 * d2 + 2.0 * d3 + d4)
            for s, d1, d2, d3, d4 in zip(state, k1, k2, k3, k4)
        ]

        t_next = t + dt
        x_next, y_next, vx_next, vy_next = next_state

        if y_next < 0.0:
            landing_point = _interpolate_landing(
                t, state[0], state[1], state[2], state[3],
                t_next, x_next, y_next, vx_next, vy_next,
                mass, g
            )
            points.append(landing_point)
            break

        points.append(_create_point_dict(t_next, x_next, y_next, vx_next, vy_next, mass, g))

        t = t_next
        state = next_state

    return {
        "summary": _compute_summary(points),
        "points": points,
    }


def simulate_projectile(
    v0: float,
    angle_deg: float,
    mass: float,
    k: float,
    wind_x: float,
    g: float = 9.81,
    dt: float = 0.01,
) -> Dict[str, Any]:
    """
    Main entrypoint to compute three trajectory arrays simultaneously:
    1. Ideal (no drag, analytical)
    2. Drag with Euler Integration
    3. Drag with Runge-Kutta 4th Order (RK4) Integration

    Parameters:
        v0 (float): Initial launch speed (m/s)
        angle_deg (float): Launch angle above horizontal in degrees (0 to 90)
        mass (float): Projectile mass (kg)
        k (float): Drag coefficient constant (kg/m)
        wind_x (float): Wind speed along x-axis (m/s), positive is with motion
        g (float): Acceleration due to gravity (m/s^2), default 9.81
        dt (float): Time step increment for integration (s), default 0.01

    Returns:
        Clean dictionary containing input parameters and all three trajectory datasets
        with points and summary metrics.
    """
    angle_rad = math.radians(angle_deg)

    ideal_result = _simulate_ideal(v0=v0, angle_rad=angle_rad, mass=mass, g=g, dt=dt)
    euler_result = _simulate_euler(v0=v0, angle_rad=angle_rad, mass=mass, k=k, wind_x=wind_x, g=g, dt=dt)
    rk4_result = _simulate_rk4(v0=v0, angle_rad=angle_rad, mass=mass, k=k, wind_x=wind_x, g=g, dt=dt)

    return {
        "parameters": {
            "v0": v0,
            "angle_deg": angle_deg,
            "mass": mass,
            "k": k,
            "wind_x": wind_x,
            "g": g,
            "dt": dt,
        },
        "trajectories": {
            "ideal": ideal_result,
            "euler": euler_result,
            "rk4": rk4_result,
        },
    }
