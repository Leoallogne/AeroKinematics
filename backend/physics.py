"""
Physics simulation module for 2D Projectile Motion.
Supports:
1. Ideal, Euler, and RK4 trajectories with relative aerodynamic drag and wind vectors.
2. Altitude-dependent atmospheric density (barometric decay) & variable gravity.
3. Fast Monte Carlo dispersion simulation for impact point scatter analysis.
4. CSV generation for trajectory energy and kinematic telemetry.
"""

from typing import Dict, Any, List, Tuple
import math
import numpy as np

# Physical Constants
R_EARTH = 6371000.0  # Earth's mean radius in meters
SCALE_HEIGHT = 8500.0  # Atmospheric scale height in meters


def _calculate_derivatives(
    y: float,
    vx: float,
    vy: float,
    mass: float,
    k: float,
    wind_x: float,
    wind_y: float,
    g: float,
    use_variable_atmosphere: bool = False,
) -> Tuple[float, float]:
    """
    Computes accelerations ax and ay given current state, drag, wind, and atmospheric conditions.

    If use_variable_atmosphere is True:
      - Barometric density decay: k(y) = k_0 * exp(-max(0, y) / 8500)
      - Gravitational altitude decay: g(y) = g_0 * (R_earth / (R_earth + max(0, y)))^2
    """
    clamped_y = max(0.0, y)

    if use_variable_atmosphere:
        # Barometric density decay
        k_eff = k * math.exp(-clamped_y / SCALE_HEIGHT)
        # Gravitational decay with altitude
        g_eff = g * ((R_EARTH / (R_EARTH + clamped_y)) ** 2)
    else:
        k_eff = k
        g_eff = g

    v_rel_x = vx - wind_x
    v_rel_y = vy - wind_y
    v_rel = math.sqrt(v_rel_x**2 + v_rel_y**2)
    drag_factor = (k_eff / mass) * v_rel if mass > 0 else 0.0

    ax = -drag_factor * v_rel_x
    ay = -g_eff - drag_factor * v_rel_y
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
    Linearly interpolates state when y_next < 0 to find exact ground impact point (y = 0.0).
    """
    if y_curr == y_prev:
        fraction = 0.0
    else:
        fraction = (0.0 - y_prev) / (y_curr - y_prev)
    fraction = max(0.0, min(1.0, fraction))

    t_final = t_prev + fraction * (t_curr - t_prev)
    x_final = x_prev + fraction * (x_curr - x_prev)
    y_final = 0.0
    vx_final = vx_prev + fraction * (vx_curr - vx_prev)
    vy_final = vy_prev + fraction * (vy_curr - vy_prev)

    return _create_point_dict(t_final, x_final, y_final, vx_final, vy_final, mass, g)


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

    x_final = vx0 * t_flight
    y_final = 0.0
    vx_final = vx0
    vy_final = vy0 - g * t_flight
    points.append(_create_point_dict(t_flight, x_final, y_final, vx_final, vy_final, mass, g))

    return {
        "summary": _compute_summary(points),
        "points": points,
    }


def _simulate_euler(
    v0: float,
    angle_rad: float,
    mass: float,
    k: float,
    wind_x: float,
    wind_y: float,
    g: float,
    dt: float,
    use_variable_atmosphere: bool = False,
    max_steps: int = 100_000,
):
    """
    Numerical trajectory using Euler's integration method.
    """
    t = 0.0
    x = 0.0
    y = 0.0
    vx = v0 * math.cos(angle_rad)
    vy = v0 * math.sin(angle_rad)

    points: List[Dict[str, float]] = [_create_point_dict(t, x, y, vx, vy, mass, g)]

    for _ in range(max_steps):
        ax, ay = _calculate_derivatives(y, vx, vy, mass, k, wind_x, wind_y, g, use_variable_atmosphere)

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


def _simulate_rk4(
    v0: float,
    angle_rad: float,
    mass: float,
    k: float,
    wind_x: float,
    wind_y: float,
    g: float,
    dt: float,
    use_variable_atmosphere: bool = False,
    max_steps: int = 100_000,
):
    """
    Numerical trajectory using 4th Order Runge-Kutta (RK4) integration.
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
        ax, ay = _calculate_derivatives(_y, _vx, _vy, mass, k, wind_x, wind_y, g, use_variable_atmosphere)
        return [_vx, _vy, ax, ay]

    state = [x, y, vx, vy]

    for _ in range(max_steps):
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
    wind_x: float = 0.0,
    wind_y: float = 0.0,
    g: float = 9.81,
    dt: float = 0.01,
    use_variable_atmosphere: bool = False,
) -> Dict[str, Any]:
    """
    Main entrypoint to compute three trajectory arrays simultaneously:
    1. Ideal (no drag, analytical)
    2. Drag with Euler Integration
    3. Drag with Runge-Kutta 4th Order (RK4) Integration
    """
    angle_rad = math.radians(angle_deg)

    ideal_result = _simulate_ideal(v0=v0, angle_rad=angle_rad, mass=mass, g=g, dt=dt)
    euler_result = _simulate_euler(
        v0=v0, angle_rad=angle_rad, mass=mass, k=k, wind_x=wind_x, wind_y=wind_y, g=g, dt=dt,
        use_variable_atmosphere=use_variable_atmosphere
    )
    rk4_result = _simulate_rk4(
        v0=v0, angle_rad=angle_rad, mass=mass, k=k, wind_x=wind_x, wind_y=wind_y, g=g, dt=dt,
        use_variable_atmosphere=use_variable_atmosphere
    )

    return {
        "parameters": {
            "v0": v0,
            "angle_deg": angle_deg,
            "mass": mass,
            "k": k,
            "wind_x": wind_x,
            "wind_y": wind_y,
            "g": g,
            "dt": dt,
            "use_variable_atmosphere": use_variable_atmosphere,
        },
        "trajectories": {
            "ideal": ideal_result,
            "euler": euler_result,
            "rk4": rk4_result,
        },
    }


def _fast_rk4_impact(
    v0: float,
    angle_rad: float,
    mass: float,
    k: float,
    wind_x: float,
    wind_y: float,
    g: float,
    dt: float,
    use_variable_atmosphere: bool = False,
    max_steps: int = 50_000,
) -> Tuple[float, float]:
    """
    Optimized RK4 solver returning only the final impact range (x_final) and flight time (t_final).
    Used for high-throughput Monte Carlo dispersion simulation.
    """
    vx0 = v0 * math.cos(angle_rad)
    vy0 = v0 * math.sin(angle_rad)

    if vy0 <= 0:
        return 0.0, 0.0

    state = [0.0, 0.0, vx0, vy0]
    t = 0.0

    def derivatives(s):
        _x, _y, _vx, _vy = s
        ax, ay = _calculate_derivatives(_y, _vx, _vy, mass, k, wind_x, wind_y, g, use_variable_atmosphere)
        return [_vx, _vy, ax, ay]

    for _ in range(max_steps):
        k1 = derivatives(state)
        s2 = [s + 0.5 * dt * d for s, d in zip(state, k1)]
        k2 = derivatives(s2)
        s3 = [s + 0.5 * dt * d for s, d in zip(state, k2)]
        k3 = derivatives(s3)
        s4 = [s + dt * d for s, d in zip(state, k3)]
        k4 = derivatives(s4)

        next_state = [
            s + (dt / 6.0) * (d1 + 2.0 * d2 + 2.0 * d3 + d4)
            for s, d1, d2, d3, d4 in zip(state, k1, k2, k3, k4)
        ]
        t_next = t + dt

        if next_state[1] < 0.0:
            fraction = (0.0 - state[1]) / (next_state[1] - state[1])
            x_final = state[0] + fraction * (next_state[0] - state[0])
            t_final = t + fraction * dt
            return x_final, t_final

        t = t_next
        state = next_state

    return state[0], t


def simulate_monte_carlo(
    v0: float,
    angle_deg: float,
    mass: float,
    k: float,
    wind_x: float,
    wind_y: float,
    g: float,
    dt: float,
    use_variable_atmosphere: bool,
    num_simulations: int,
    v0_std_dev: float,
    angle_std_dev: float,
) -> Dict[str, Any]:
    """
    Performs Monte Carlo dispersion simulation using Gaussian distributions on v0 and angle.
    Returns impact scatter coordinates and statistical metrics.
    """
    rng = np.random.default_rng()

    # Generate N random samples with Gaussian noise
    v0_samples = rng.normal(loc=v0, scale=v0_std_dev, size=num_simulations)
    v0_samples = np.clip(v0_samples, 0.1, 2500.0)  # Ensure positive velocity

    angle_samples = rng.normal(loc=angle_deg, scale=angle_std_dev, size=num_simulations)
    angle_samples = np.clip(angle_samples, 0.1, 89.9)  # Keep in realistic projectile angle bounds

    impact_points: List[Dict[str, float]] = []
    ranges: List[float] = []

    for i in range(num_simulations):
        v_sample = float(v0_samples[i])
        a_sample = float(angle_samples[i])
        a_rad = math.radians(a_sample)

        x_impact, t_flight = _fast_rk4_impact(
            v0=v_sample,
            angle_rad=a_rad,
            mass=mass,
            k=k,
            wind_x=wind_x,
            wind_y=wind_y,
            g=g,
            dt=dt,
            use_variable_atmosphere=use_variable_atmosphere,
        )

        impact_points.append({
            "x": round(x_impact, 4),
            "y": 0.0,
            "flight_time": round(t_flight, 4),
            "v0": round(v_sample, 2),
            "angle_deg": round(a_sample, 2),
        })
        ranges.append(x_impact)

    range_arr = np.array(ranges, dtype=np.float64)
    mean_range = float(np.mean(range_arr))
    std_dev_range = float(np.std(range_arr, ddof=1)) if num_simulations > 1 else 0.0
    min_range = float(np.min(range_arr))
    max_range = float(np.max(range_arr))

    # 95% confidence interval margin for the mean (1.96 * std / sqrt(N))
    ci_95_mean_margin = float(1.96 * std_dev_range / math.sqrt(num_simulations))
    # 95% dispersion radius of the projectile scatter (1.96 * sigma)
    dispersion_radius_95 = float(1.96 * std_dev_range)

    return {
        "num_simulations": num_simulations,
        "base_parameters": {
            "v0": v0,
            "angle_deg": angle_deg,
            "v0_std_dev": v0_std_dev,
            "angle_std_dev": angle_std_dev,
            "mass": mass,
            "k": k,
            "wind_x": wind_x,
            "wind_y": wind_y,
            "g": g,
            "dt": dt,
            "use_variable_atmosphere": use_variable_atmosphere,
        },
        "summary": {
            "mean_range": round(mean_range, 4),
            "std_dev_range": round(std_dev_range, 4),
            "min_range": round(min_range, 4),
            "max_range": round(max_range, 4),
            "ci_95_mean_margin": round(ci_95_mean_margin, 4),
            "dispersion_radius_95": round(dispersion_radius_95, 4),
        },
        "impact_points": impact_points,
    }


def generate_trajectory_csv(points: List[Dict[str, float]]) -> str:
    """
    Generates CSV content with columns:
    time,x,y,vx,vy,kinetic_energy,potential_energy,total_energy
    """
    lines = ["time,x,y,vx,vy,kinetic_energy,potential_energy,total_energy"]
    for p in points:
        lines.append(
            f"{p.get('time', 0.0):.4f},{p.get('x', 0.0):.4f},{p.get('y', 0.0):.4f},"
            f"{p.get('vx', 0.0):.4f},{p.get('vy', 0.0):.4f},"
            f"{p.get('Ek', 0.0):.4f},{p.get('Ep', 0.0):.4f},{p.get('Em', 0.0):.4f}"
        )
    return "\r\n".join(lines)
