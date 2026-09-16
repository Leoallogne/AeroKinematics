# 📐 AeroKinematics: Mathematical Foundations & Physical Derivations

This document provides a comprehensive, rigorous mathematical derivation of the physics, differential equations of motion, numerical integration techniques, atmospheric models, and statistical dispersion algorithms implemented in the **AeroKinematics 2D Projectile Simulator**.

---

## 📑 Table of Contents
1. [Coordinate System & Initial Conditions](#1-coordinate-system--initial-conditions)
2. [Analytical Ideal Trajectory (Vacuum)](#2-analytical-ideal-trajectory-vacuum)
3. [Aerodynamic Drag with 2D Wind Vectors](#3-aerodynamic-drag-with-2d-wind-vectors)
4. [High-Altitude Atmospheric & Gravitational Decay](#4-high-altitude-atmospheric--gravitational-decay)
5. [Numerical Integration Methods](#5-numerical-integration-methods)
   - [Euler Integration (1st Order)](#51-euler-integration-1st-order)
   - [Runge-Kutta 4th Order (RK4) Method](#52-runge-kutta-4th-order-rk4-method)
6. [Ground Landing Linear Interpolation](#6-ground-landing-linear-interpolation)
7. [Mechanical Energy & Dissipation Rates](#7-mechanical-energy--dissipation-rates)
8. [Monte Carlo Dispersion & Statistical Analysis](#8-monte-carlo-dispersion--statistical-analysis)

---

## 1. Coordinate System & Initial Conditions

The simulation operates in a 2D Cartesian plane where:
- $\hat{i}$ points horizontally along the ground in the direction of the initial launch component ($+x$).
- $\hat{j}$ points vertically upward perpendicular to the ground ($+y$).
- The origin $(0, 0)$ is situated at ground level at the launch point.

Given:
- Initial launch speed $v_0 \in \mathbb{R}^+$
- Launch angle $\theta \in [0^\circ, 90^\circ]$ above the horizontal

The initial velocity state vector $\vec{v}(0)$ is decomposed into Cartesian components:
$$v_{x0} = v_0 \cos\theta$$
$$v_{y0} = v_0 \sin\theta$$

Initial state vector at $t = 0$:
$$\vec{S}(0) = \begin{bmatrix} x(0) \\ y(0) \\ v_x(0) \\ v_y(0) \end{bmatrix} = \begin{bmatrix} 0 \\ 0 \\ v_{x0} \\ v_{y0} \end{bmatrix}$$

---

## 2. Analytical Ideal Trajectory (Vacuum)

In an idealized vacuum state with uniform constant gravitational acceleration $g$, aerodynamic drag is absent ($\vec{F}_{\text{drag}} = 0$).

### 2.1 Equations of Motion
Applying Newton's Second Law:
$$\sum F_x = m \frac{d^2 x}{dt^2} = 0 \implies a_x(t) = 0$$
$$\sum F_y = m \frac{d^2 y}{dt^2} = -m g \implies a_y(t) = -g$$

Integrating with respect to time $t$:
$$v_x(t) = v_{x0}$$
$$v_y(t) = v_{y0} - g t$$

Integrating again yields positions:
$$x(t) = v_{x0} t$$
$$y(t) = v_{y0} t - \frac{1}{2} g t^2$$

### 2.2 Critical Trajectory Metrics
1. **Time of Flight ($T_{\text{flight}}$)**:
   Setting $y(T) = 0$ for $T > 0$:
   $$v_{y0} T - \frac{1}{2} g T^2 = 0 \implies T_{\text{flight}} = \frac{2 v_{y0}}{g} = \frac{2 v_0 \sin\theta}{g}$$

2. **Maximum Altitude / Apogee ($H_{\max}$)**:
   Occurs when the vertical velocity vanishes: $v_y(t_{\text{peak}}) = 0 \implies t_{\text{peak}} = \frac{v_{y0}}{g}$.
   $$H_{\max} = y(t_{\text{peak}}) = v_{y0}\left(\frac{v_{y0}}{g}\right) - \frac{1}{2} g \left(\frac{v_{y0}}{g}\right)^2 = \frac{v_{y0}^2}{2g} = \frac{v_0^2 \sin^2\theta}{2g}$$

3. **Maximum Horizontal Range ($R_{\max}$)**:
   Substituting $T_{\text{flight}}$ into horizontal position:
   $$R_{\max} = x(T_{\text{flight}}) = v_{x0} \left(\frac{2 v_{y0}}{g}\right) = \frac{2 v_0^2 \sin\theta \cos\theta}{g} = \frac{v_0^2 \sin(2\theta)}{g}$$

---

## 3. Aerodynamic Drag with 2D Wind Vectors

In a realistic fluid medium (air), an object moving at high Reynolds numbers experiences quadratic aerodynamic drag.

### 3.1 Relative Velocity Vector
Let the ambient wind velocity vector be $\vec{w} = w_x \hat{i} + w_y \hat{j}$. The motion of the projectile relative to the fluid is:
$$\vec{v}_{\text{rel}} = \vec{v} - \vec{w} = (v_x - w_x)\hat{i} + (v_y - w_y)\hat{j}$$

The scalar magnitude of relative speed is:
$$v_{\text{rel}} = \|\vec{v}_{\text{rel}}\| = \sqrt{(v_x - w_x)^2 + (v_y - w_y)^2}$$

The unit vector opposing fluid motion is:
$$\hat{u}_{\text{drag}} = -\frac{\vec{v}_{\text{rel}}}{v_{\text{rel}}}$$

### 3.2 Drag Force Equation
The aerodynamic drag force vector $\vec{F}_d$ acts antiparallel to $\vec{v}_{\text{rel}}$:
$$\vec{F}_d = -\frac{1}{2} \rho C_d A v_{\text{rel}} \vec{v}_{\text{rel}}$$

where:
- $\rho$: Fluid air density ($\text{kg/m}^3$)
- $C_d$: Drag coefficient of the body
- $A$: Cross-sectional frontal area ($\text{m}^2$)

Grouping the parameters into a lumped drag parameter $k$:
$$k = \frac{1}{2} \rho C_d A \quad [\text{kg/m}]$$

Thus:
$$\vec{F}_d = -k v_{\text{rel}} \vec{v}_{\text{rel}}$$

### 3.3 Coupled Equations of Acceleration
Including gravity $\vec{F}_g = -m g \hat{j}$:
$$\vec{F}_{\text{net}} = \vec{F}_d + \vec{F}_g = -k v_{\text{rel}} \vec{v}_{\text{rel}} - m g \hat{j}$$

Dividing by mass $m$ yields the coupled non-linear differential equations:
$$a_x = \frac{dv_x}{dt} = -\left(\frac{k}{m}\right) v_{\text{rel}} (v_x - w_x)$$
$$a_y = \frac{dv_y}{dt} = -g - \left(\frac{k}{m}\right) v_{\text{rel}} (v_y - w_y)$$

---

## 4. High-Altitude Atmospheric & Gravitational Decay

For high-speed or high-apogee sub-orbital projectiles, assuming constant sea-level air density and surface gravity introduces significant errors.

```
       Altitude (y)
          ▲
          │    Outer Atmosphere: Low Density, Low Drag
          │    -----------------------------------------
          │    ρ(y) = ρ₀ · exp(-y / 8500)
          │    g(y) = g₀ · [R_earth / (R_earth + y)]²
          │
          │    Sea Level (y = 0):
          │    ρ = ρ₀ (1.225 kg/m³), g = 9.81 m/s²
          └────────────────────────────────────────► Horizontal (x)
```

### 4.1 Barometric Atmospheric Density Decay
According to the isothermal barometric formula, atmospheric pressure and density decay exponentially with altitude $y$:
$$\rho(y) = \rho_0 \exp\left(-\frac{y}{H}\right)$$

where:
- $\rho_0$: Sea-level atmospheric air density ($1.225\text{ kg/m}^3$)
- $H$: Atmospheric scale height ($\approx 8500\text{ meters}$)

The dynamic drag coefficient at altitude $y$ becomes:
$$k(y) = k_0 \left(\frac{\rho(y)}{\rho_0}\right) = k_0 \exp\left(-\frac{\max(0, y)}{8500}\right)$$

### 4.2 Variable Gravity (Newton's Law of Gravitation)
From Newton's Law of Universal Gravitation:
$$g(y) = G \frac{M_{\text{earth}}}{(R_{\text{earth}} + y)^2}$$

At surface level $y = 0$, $g_0 = G \frac{M_{\text{earth}}}{R_{\text{earth}}^2} \approx 9.81\text{ m/s}^2$. Therefore:
$$g(y) = g_0 \left(\frac{R_{\text{earth}}}{R_{\text{earth}} + \max(0, y)}\right)^2$$

where Earth's volumetric mean radius is $R_{\text{earth}} = 6\,371\,000\text{ meters}$.

---

## 5. Numerical Integration Methods

Because the differential equations in Section 3 and 4 are non-linear and coupled, analytical closed-form solutions do not exist. Numerical integration solves for the state vector step-by-step:
$$\vec{S} = [x, y, v_x, v_y]^T, \quad \frac{d\vec{S}}{dt} = \vec{f}(t, \vec{S}) = \begin{bmatrix} v_x \\ v_y \\ a_x(y, v_x, v_y) \\ a_y(y, v_x, v_y) \end{bmatrix}$$

### 5.1 Euler Integration (1st Order)
Euler's method approximates derivatives using forward finite differences:
$$\vec{S}_{n+1} = \vec{S}_n + \Delta t \cdot \vec{f}(t_n, \vec{S}_n)$$

Component-wise:
$$x_{n+1} = x_n + v_{x,n} \Delta t$$
$$y_{n+1} = y_n + v_{y,n} \Delta t$$
$$v_{x,n+1} = v_{x,n} + a_{x,n} \Delta t$$
$$v_{y,n+1} = v_{y,n} + a_{y,n} \Delta t$$
$$t_{n+1} = t_n + \Delta t$$

- **Local Truncation Error**: $\mathcal{O}(\Delta t^2)$
- **Global Error**: $\mathcal{O}(\Delta t)$
- *Characteristics*: Computationally fast, but accumulates numerical phase and energy drift over long flight durations.

### 5.2 Runge-Kutta 4th Order (RK4) Method
The classical RK4 method samples derivatives at four stages within each time-step interval $[t_n, t_n + \Delta t]$:

1. **Stage 1 (Initial Slope)**:
   $$\vec{k}_1 = \vec{f}(t_n, \vec{S}_n)$$

2. **Stage 2 (Midpoint Slope 1)**:
   $$\vec{k}_2 = \vec{f}\left(t_n + \frac{\Delta t}{2}, \vec{S}_n + \frac{\Delta t}{2} \vec{k}_1\right)$$

3. **Stage 3 (Midpoint Slope 2)**:
   $$\vec{k}_3 = \vec{f}\left(t_n + \frac{\Delta t}{2}, \vec{S}_n + \frac{\Delta t}{2} \vec{k}_2\right)$$

4. **Stage 4 (Endpoint Slope)**:
   $$\vec{k}_4 = \vec{f}(t_n + \Delta t, \vec{S}_n + \Delta t \vec{k}_3)$$

5. **Weighted Sum Integration**:
   $$\vec{S}_{n+1} = \vec{S}_n + \frac{\Delta t}{6} \left(\vec{k}_1 + 2\vec{k}_2 + 2\vec{k}_3 + \vec{k}_4\right)$$

- **Local Truncation Error**: $\mathcal{O}(\Delta t^5)$
- **Global Error**: $\mathcal{O}(\Delta t^4)$
- *Characteristics*: Highly accurate and stable for oscillatory and steep velocity gradients.

---

## 6. Ground Landing Linear Interpolation

At discrete integration steps, the trajectory will transition from above ground to below ground:
$$y_n \ge 0 \quad \text{and} \quad y_{n+1} < 0$$

Truncating or accepting $y_{n+1} < 0$ introduces a systematic over-shooting error. AeroKinematics calculates the exact linear intersection at $y = 0$:

```
   Altitude (y)
        ▲
   y_n  ├───● (t_n, x_n, y_n)
        │    \
        │     \
   y=0  ───────●─────────────────────► Ground
        │       \  (t_final, x_final, 0.0)
        │        \
 y_n+1  ├─────────● (t_n+1, x_n+1, y_n+1)
```

The fraction of the step elapsed when crossing $y = 0$:
$$\text{fraction} = \frac{0 - y_n}{y_{n+1} - y_n} \in [0, 1]$$

The exact terminal landing state is interpolated:
$$t_{\text{final}} = t_n + \text{fraction} \cdot \Delta t$$
$$x_{\text{final}} = x_n + \text{fraction} \cdot (x_{n+1} - x_n)$$
$$y_{\text{final}} = 0.0$$
$$v_{x,\text{final}} = v_{x,n} + \text{fraction} \cdot (v_{x,n+1} - v_{x,n})$$
$$v_{y,\text{final}} = v_{y,n} + \text{fraction} \cdot (v_{y,n+1} - v_{y,n})$$

---

## 7. Mechanical Energy & Dissipation Rates

### 7.1 Energy Components
At any time step $t$:
1. **Kinetic Energy ($E_k$)**:
   $$E_k(t) = \frac{1}{2} m \|\vec{v}(t)\|^2 = \frac{1}{2} m \left(v_x^2(t) + v_y^2(t)\right)$$

2. **Gravitational Potential Energy ($E_p$)**:
   $$E_p(t) = m g \max(0, y(t))$$

3. **Total Mechanical Energy ($E_m$)**:
   $$E_m(t) = E_k(t) + E_p(t)$$

### 7.2 Energy Dissipation Rate
By the Work-Energy Theorem:
$$\frac{dE_m}{dt} = \vec{F}_d \cdot \vec{v} = \left(-k v_{\text{rel}} \vec{v}_{\text{rel}}\right) \cdot \vec{v}$$

In the absence of wind ($\vec{w} = 0 \implies \vec{v}_{\text{rel}} = \vec{v}$):
$$\frac{dE_m}{dt} = -k \|\vec{v}\|^3 \le 0$$

Mechanical energy is monotonically dissipated into thermal energy via aerodynamic friction.

### 7.3 Total Percentage Energy Loss
$$\Delta E_m \% = \left(\frac{E_m(0) - E_m(T_{\text{flight}})}{E_m(0)}\right) \times 100\%$$

In the Ideal case: $\Delta E_m \% = 0.0\%$ (Strict conservation).

---

## 8. Monte Carlo Dispersion & Statistical Analysis

In real-world ballistics and rocketry, initial parameters exhibit stochastic uncertainty (sensor noise, propellant variations, atmospheric turbulence).

### 8.1 Gaussian Stochastic Disturbances
Initial launch velocity $v_0$ and launch angle $\theta$ are modeled as independent Gaussian random variables:
$$V_0^{(i)} \sim \mathcal{N}(\mu_{v0}, \sigma_{v0}^2)$$
$$\Theta^{(i)} \sim \mathcal{N}(\mu_\theta, \sigma_\theta^2)$$

For $N$ simulations ($i = 1, \dots, N$), the RK4 solver evaluates impact ranges $X^{(i)}$:
$$X^{(i)} = \text{RK4\_Solver}(V_0^{(i)}, \Theta^{(i)}, m, k, \vec{w})$$

### 8.2 Statistical Metrics
1. **Sample Mean Range ($\bar{X}$)**:
   $$\bar{X} = \frac{1}{N} \sum_{i=1}^N X^{(i)}$$

2. **Sample Standard Deviation ($s_X$)**:
   $$s_X = \sqrt{\frac{1}{N - 1} \sum_{i=1}^N \left(X^{(i)} - \bar{X}\right)^2}$$

3. **95% Confidence Interval for Mean Range**:
   By the Central Limit Theorem:
   $$\text{CI}_{95\%} = \bar{X} \pm 1.96 \frac{s_X}{\sqrt{N}}$$
   Margin of error radius:
   $$r_{\text{CI}} = 1.96 \frac{s_X}{\sqrt{N}}$$

4. **95% Dispersion Scatter Radius**:
   Assuming approximately normal distribution of final landing positions:
   $$r_{\text{dispersion}} = 1.96 \cdot s_X$$
   Approximately $95\%$ of all physical projectile impacts fall within $[\bar{X} - r_{\text{dispersion}}, \bar{X} + r_{\text{dispersion}}]$.
