# 🚀 AeroKinematics: 2D Projectile Physics Lab & Solver Engine

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI Framework](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Physics Solver](https://img.shields.io/badge/Solver-RK4%20%7C%20Euler%20%7C%20Ideal-cyan.svg)](#physics--mathematical-formulation)

A high-precision, interactive 2D projectile motion simulation laboratory and numerical solver built with **FastAPI** (Python backend) and a modern dark-themed **HTML5 Canvas & Chart.js** frontend.

It simultaneously computes, renders, and compares three trajectory models under aerodynamic drag, 2D wind vectors, altitude-dependent atmospheric density decay, variable gravity, and gravitational acceleration:
1. **Ideal Trajectory** (Analytical exact solution, vacuum state)
2. **Euler Method** (First-order numerical integration)
3. **Runge-Kutta 4th Order (RK4)** (High-order numerical benchmark solver)

---

## 🌟 Key Features

- ⚡ **High-Precision RK4 & Euler Solvers**: Computes initial value differential equations (ODEs) for velocity, acceleration, position, and energy dissipation.
- 🌌 **Altitude-Dependent Barometric Decay & Variable Gravity**:
  - Atmospheric density decay: $\rho(y) = \rho_0 \exp(-y / 8500)$
  - Gravitational decay over high altitudes: $g(y) = g_0 \left(\frac{R_{\text{earth}}}{R_{\text{earth}} + y}\right)^2$
- 🎯 **Monte Carlo Dispersion Simulation (`POST /api/simulate/monte-carlo`)**:
  - Simulates 50–500 stochastic projectile trajectories using Gaussian noise on initial launch speed and angle
  - Computes impact point scatter and comprehensive statistical metrics ($\mu_x, \sigma_x, \text{min}, \text{max}$, 95% Confidence Interval)
- 🌬️ **2D Aerodynamic Drag & Wind Vectoring**: Models quadratic air resistance with relative speed vectors $\vec{v}_{\text{rel}} = (v_x - w_x, v_y - w_y)$.
- 🔋 **Real-Time Mechanical Energy Tracking**: Calculates Kinetic Energy ($E_k$), Potential Energy ($E_p$), and Total Mechanical Energy ($E_m$) at every integration step.
- 🎨 **HTML5 Canvas Visualizer**:
  - Auto-scaling Cartesian grid with metric tick marks
  - Distinct high-contrast color paths (Cyan for RK4, Yellow for Euler, Slate dashed for Ideal)
  - Animated glowing projectile orb progressing in real-time frame-by-frame
  - Peak (Apogee) $H_{\max}$ and impact range $R_{\max}$ annotations
- 📊 **Synchronized Chart.js Energy Graph**: Graph traces $E_k, E_p, E_m$ in lockstep with the projectile ball's location.
- 📥 **CSV Telemetry Data Export (`POST /api/export/csv`)**: Download full numerical trajectory steps (`time, x, y, vx, vy, kinetic_energy, potential_energy, total_energy`) directly as a CSV file.
- 🔌 **FastAPI REST API**: Fully typed, non-blocking asynchronous endpoints with interactive Swagger UI (`/docs`).

---

## 📐 Physics & Mathematical Formulation

### 1. Relative Wind & Aerodynamic Drag Equations
The relative velocity vector accounting for 2D wind $(w_x, w_y)$ is:
$$v_{\text{rel}, x} = v_x - w_x, \quad v_{\text{rel}, y} = v_y - w_y$$
$$v_{\text{rel}} = \sqrt{(v_x - w_x)^2 + (v_y - w_y)^2}$$

Accelerations along the X and Y axes:
$$a_x = -\left(\frac{k(y)}{m}\right) v_{\text{rel}} (v_x - w_x)$$
$$a_y = -g(y) - \left(\frac{k(y)}{m}\right) v_{\text{rel}} (v_y - w_y)$$

### 2. Barometric Density Decay & Variable Gravity
When `use_variable_atmosphere` is enabled:
$$k(y) = k_0 \cdot \exp\left(-\frac{\max(0, y)}{8500}\right)$$
$$g(y) = g_0 \cdot \left(\frac{R_{\text{earth}}}{R_{\text{earth}} + \max(0, y)}\right)^2 \quad (R_{\text{earth}} = 6371000\text{ m})$$

### 3. Numerical Integration Methods
- **Euler Method (1st Order)**:
  $$x_{n+1} = x_n + v_{x,n} \Delta t, \quad y_{n+1} = y_n + v_{y,n} \Delta t$$
  $$v_{x,n+1} = v_{x,n} + a_{x,n} \Delta t, \quad v_{y,n+1} = v_{y,n} + a_{y,n} \Delta t$$

- **Runge-Kutta 4th Order (RK4)**:
  State vector $S = [x, y, v_x, v_y]$ with derivative function $f(t, S) = [v_x, v_y, a_x, a_y]$:
  $$k_1 = f(t_n, S_n)$$
  $$k_2 = f\left(t_n + \frac{\Delta t}{2}, S_n + \frac{\Delta t}{2} k_1\right)$$
  $$k_3 = f\left(t_n + \frac{\Delta t}{2}, S_n + \frac{\Delta t}{2} k_2\right)$$
  $$k_4 = f(t_n + \Delta t, S_n + \Delta t \, k_3)$$
  $$S_{n+1} = S_n + \frac{\Delta t}{6} (k_1 + 2k_2 + 2k_3 + k_4)$$

- **Ground Impact Linear Interpolation**:
  When $y_{n+1} < 0$, the exact landing point is resolved via linear interpolation:
  $$\text{fraction} = \frac{0 - y_n}{y_{n+1} - y_n}, \quad x_{\text{final}} = x_n + \text{fraction} \cdot (x_{n+1} - x_n), \quad t_{\text{final}} = t_n + \text{fraction} \cdot \Delta t$$

### 4. Energy Formulation
- Kinetic Energy: $E_k = \frac{1}{2} m (v_x^2 + v_y^2)$
- Potential Energy: $E_p = m g \max(0, y)$
- Total Mechanical Energy: $E_m = E_k + E_p$

---

## 🏗️ Architecture

```
AeroKinematics/
├── backend/
│   ├── __init__.py
│   ├── main.py          # FastAPI application server (Simulate, Monte Carlo, CSV Export)
│   └── physics.py       # Physics simulation engine (Ideal, Euler, RK4, Monte Carlo, Atm decay)
├── frontend/
│   ├── index.html       # Dashboard UI with Tailwind CSS
│   ├── style.css        # Custom dark theme, glassmorphism, slider styling
│   └── app.js           # Canvas renderer, Chart.js graph, controls, CSV exporter
├── requirements.txt     # Python backend dependencies
├── test_backend.py      # Automated physics & API test suite
└── README.md
```

---

## ⚡ Quickstart & Installation

### Prerequisites
- Python 3.11 or higher
- Modern web browser

### 1. Clone & Setup Backend
```bash
git clone https://github.com/Leoallogne/AeroKinematics.git
cd AeroKinematics

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Backend Server
```bash
python backend/main.py
# or: uvicorn backend.main:app --reload --port 8000
```
FastAPI server will launch on `http://localhost:8000`. Interactive API documentation is available at `http://localhost:8000/docs`.

### 3. Launch Frontend
Open `frontend/index.html` directly in your browser, or serve via Python static server:
```bash
python -m http.server 3000 --directory frontend
```
Navigate to `http://localhost:3000` in your web browser.

---

## 🧪 Automated Testing

Run the automated test suite verifying physics calculations, variable atmosphere, Monte Carlo dispersion, and API endpoints:
```bash
python test_backend.py
```

---

## 📡 API Reference

### 1. `POST /api/simulate`
Computes all 3 trajectory models simultaneously.

**Request Body:**
```json
{
  "v0": 100.0,
  "angle_deg": 45.0,
  "mass": 2.0,
  "k": 0.01,
  "wind_x": -3.0,
  "wind_y": 0.0,
  "g": 9.81,
  "dt": 0.01,
  "use_variable_atmosphere": true
}
```

---

### 2. `POST /api/simulate/monte-carlo`
Executes $N$ stochastic simulations with Gaussian noise on initial launch speed and angle.

**Request Body:**
```json
{
  "v0": 100.0,
  "angle_deg": 45.0,
  "mass": 2.0,
  "k": 0.01,
  "wind_x": -3.0,
  "wind_y": 0.0,
  "g": 9.81,
  "dt": 0.01,
  "use_variable_atmosphere": true,
  "num_simulations": 150,
  "v0_std_dev": 2.5,
  "angle_std_dev": 1.0
}
```

**Response Output:**
```json
{
  "num_simulations": 150,
  "summary": {
    "mean_range": 354.21,
    "std_dev_range": 12.45,
    "min_range": 322.18,
    "max_range": 387.94,
    "ci_95_mean_margin": 1.99,
    "dispersion_radius_95": 24.40
  },
  "impact_points": [
    { "x": 352.1, "y": 0.0, "flight_time": 9.42, "v0": 99.8, "angle_deg": 44.9 },
    ...
  ]
}
```

---

### 3. `POST /api/export/csv`
Returns a downloadable CSV file containing trajectory telemetry.

**Request Body:**
```json
{
  "v0": 100.0,
  "angle_deg": 45.0,
  "mass": 2.0,
  "k": 0.01,
  "wind_x": 0.0,
  "wind_y": 0.0,
  "g": 9.81,
  "dt": 0.01,
  "method": "rk4"
}
```

**CSV Content Headers:**
```csv
time,x,y,vx,vy,kinetic_energy,potential_energy,total_energy
```

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for details.
