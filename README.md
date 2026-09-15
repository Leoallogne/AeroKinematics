# 🚀 AeroKinematics: 2D Projectile Physics Lab & Solver Engine

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI Framework](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Physics Solver](https://img.shields.io/badge/Solver-RK4%20%7C%20Euler%20%7C%20Ideal-cyan.svg)](#physics--mathematical-formulation)

A high-precision, interactive 2D projectile motion simulation laboratory and numerical solver built with **FastAPI** (Python backend) and a modern dark-themed **HTML5 Canvas & Chart.js** frontend.

It simultaneously computes, renders, and compares three trajectory models under aerodynamic drag, horizontal wind resistance, and gravitational acceleration:
1. **Ideal Trajectory** (Analytical exact solution, vacuum state)
2. **Euler Method** (First-order numerical integration)
3. **Runge-Kutta 4th Order (RK4)** (High-order numerical benchmark solver)

---

## 🌟 Key Features

- ⚡ **High-Precision RK4 & Euler Solvers**: Computes initial value differential equations (ODEs) for velocity, acceleration, position, and energy dissipation.
- 🌬️ **Aerodynamic Drag & Wind Velocity Vectoring**: Models quadratic air resistance with relative speed vectors $\vec{v}_{\text{rel}} = (v_x - w_x, v_y)$.
- 🔋 **Real-Time Mechanical Energy Tracking**: Calculates Kinetic Energy ($E_k$), Potential Energy ($E_p$), and Total Mechanical Energy ($E_m$) at every integration step.
- 🎨 **HTML5 Canvas Visualizer**:
  - Auto-scaling Cartesian grid with metric tick marks
  - Distinct high-contrast color paths (Cyan for RK4, Yellow for Euler, Slate dashed for Ideal)
  - Animated glowing projectile orb progressing in real-time frame-by-frame
  - Interactive hover crosshairs displaying exact coordinates $(x, y)$
  - Peak (Apogee) $H_{\max}$ and impact range $R_{\max}$ annotations
- 📊 **Synchronized Chart.js Energy Graph**: Graph traces $E_k, E_p, E_m$ in lockstep with the projectile ball's location.
- 📥 **CSV Telemetry Export**: Download full numerical trajectory steps ($t, x, y, v_x, v_y, E_k, E_p, E_m$) directly to `.csv`.
- 🔌 **FastAPI REST API**: Fully documented CORS-enabled API endpoints with interactive Swagger UI (`/docs`).

---

## 📐 Physics & Mathematical Formulation

### 1. Relative Wind & Aerodynamic Drag Equations
The relative velocity vector accounting for horizontal wind $w_x$ is:
$$v_{\text{rel}, x} = v_x - w_x$$
$$v_{\text{rel}} = \sqrt{(v_x - w_x)^2 + v_y^2}$$

Accelerations along the X and Y axes:
$$a_x = -\left(\frac{k}{m}\right) v_{\text{rel}} (v_x - w_x)$$
$$a_y = -g - \left(\frac{k}{m}\right) v_{\text{rel}} v_y$$

where:
- $k$: Aerodynamic drag coefficient constant ($\text{kg/m}$)
- $m$: Projectile mass ($\text{kg}$)
- $g$: Gravitational acceleration ($9.81\text{ m/s}^2$)

### 2. Numerical Integration Methods
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

### 3. Energy Formulation
- Kinetic Energy: $E_k = \frac{1}{2} m (v_x^2 + v_y^2)$
- Potential Energy: $E_p = m g \max(0, y)$
- Total Mechanical Energy: $E_m = E_k + E_p$

---

## 🏗️ Architecture

```
AeroKinematics/
├── backend/
│   ├── __init__.py
│   ├── main.py          # FastAPI application server with CORS and /api/simulate
│   └── physics.py       # Physics simulation engine (Ideal, Euler, RK4)
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
- Modern web browser (Chrome, Firefox, Edge, Safari)

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

Run the automated test suite verifying physics trajectory calculations and API responses:
```bash
python test_backend.py
```

---

## 📡 API Reference

### `POST /api/simulate`
Computes all 3 trajectory models simultaneously.

**Request Payload:**
```json
{
  "v0": 50.0,
  "angle_deg": 45.0,
  "mass": 1.0,
  "k": 0.01,
  "wind_x": -5.0,
  "g": 9.81,
  "dt": 0.01
}
```

**Response Output:**
```json
{
  "parameters": { "v0": 50.0, "angle_deg": 45.0, ... },
  "trajectories": {
    "ideal": { "summary": { "max_height": 63.7, "max_range": 254.8, ... }, "points": [ ... ] },
    "euler": { "summary": { "max_height": 34.8, "max_range": 97.4, ... }, "points": [ ... ] },
    "rk4":   { "summary": { "max_height": 34.7, "max_range": 97.4, ... }, "points": [ ... ] }
  }
}
```

---

## 🛠️ Built With

- **Backend**: Python 3.11, FastAPI, Pydantic, Uvicorn
- **Frontend**: HTML5 Canvas API, Tailwind CSS, Vanilla JS (ES6+), Chart.js
- **Testing**: Pytest / FastAPI TestClient

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for details.
