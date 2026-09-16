"""
FastAPI Backend for 2D Projectile Motion Simulation.
Provides REST API endpoints for:
1. Standard trajectory simulation (Ideal, Euler, RK4) with optional altitude-dependent atmosphere & gravity.
2. Monte Carlo dispersion simulation for statistical impact scatter analysis.
3. CSV data export with formatted kinematic and energy telemetry download.
"""

import os
import sys
from pathlib import Path

# Add project root directory to sys.path so 'python backend/main.py' and 'python -m backend.main' both work seamlessly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Dict, Any, Optional
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from backend.physics import (
    simulate_projectile,
    simulate_monte_carlo,
    generate_trajectory_csv,
)


app = FastAPI(
    title="2D Projectile Motion Simulation API",
    description="Advanced trajectory, variable atmosphere, Monte Carlo dispersion, and telemetry export API.",
    version="1.2.0",
)

# Enable CORS for local frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SimulationRequest(BaseModel):
    v0: float = Field(..., gt=0.0, le=2500.0, description="Initial velocity in m/s (0 < v0 <= 2500)")
    angle_deg: float = Field(45.0, ge=0.0, le=90.0, description="Launch angle in degrees (0 <= angle <= 90)")
    mass: float = Field(..., gt=0.0, description="Projectile mass in kg (mass > 0)")
    k: float = Field(0.01, ge=0.0, description="Aerodynamic drag coefficient (k >= 0)")
    wind_x: float = Field(0.0, description="Wind speed along horizontal X axis (m/s)")
    wind_y: float = Field(0.0, description="Wind speed along vertical Y axis (m/s)")
    g: float = Field(9.81, gt=0.0, description="Gravitational acceleration in m/s^2 (g > 0)")
    dt: float = Field(0.01, gt=0.0, le=0.1, description="Simulation time step in seconds (0 < dt <= 0.1)")
    use_variable_atmosphere: bool = Field(
        False,
        description="Toggle barometric air density decay (H=8500m) and altitude-dependent gravity",
    )

    @model_validator(mode="before")
    @classmethod
    def check_angle_alias(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "angle" in data and "angle_deg" not in data:
                data["angle_deg"] = data["angle"]
        return data

    model_config = {
        "json_schema_extra": {
            "example": {
                "v0": 50.0,
                "angle_deg": 45.0,
                "mass": 1.0,
                "k": 0.01,
                "wind_x": -5.0,
                "wind_y": 0.0,
                "g": 9.81,
                "dt": 0.01,
                "use_variable_atmosphere": False,
            }
        }
    }


class MonteCarloRequest(SimulationRequest):
    num_simulations: int = Field(100, ge=50, le=500, description="Number of Monte Carlo simulations (50 to 500)")
    v0_std_dev: float = Field(2.0, ge=0.0, description="Standard deviation for initial velocity Gaussian noise (m/s)")
    angle_std_dev: float = Field(1.0, ge=0.0, description="Standard deviation for launch angle Gaussian noise (degrees)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "v0": 100.0,
                "angle_deg": 45.0,
                "mass": 2.0,
                "k": 0.01,
                "wind_x": -2.0,
                "wind_y": 0.0,
                "g": 9.81,
                "dt": 0.01,
                "use_variable_atmosphere": True,
                "num_simulations": 150,
                "v0_std_dev": 3.0,
                "angle_std_dev": 1.5,
            }
        }
    }


class CSVExportRequest(SimulationRequest):
    method: str = Field("rk4", description="Trajectory model to export ('rk4', 'euler', or 'ideal')")


@app.get("/api/info")
async def api_info():
    """Service information and status endpoint."""
    return {
        "status": "online",
        "service": "2D Projectile Motion Simulation API",
        "version": "1.2.0",
        "docs_url": "/docs",
    }


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/simulate")
async def run_simulation(params: SimulationRequest) -> Dict[str, Any]:
    """
    Simulates 2D projectile motion comparing Ideal, Euler, and RK4 trajectories
    with optional barometric atmospheric decay and variable gravity.
    Runs asynchronously without blocking the event loop.
    """
    try:
        results = await asyncio.to_thread(
            simulate_projectile,
            v0=params.v0,
            angle_deg=params.angle_deg,
            mass=params.mass,
            k=params.k,
            wind_x=params.wind_x,
            wind_y=params.wind_y,
            g=params.g,
            dt=params.dt,
            use_variable_atmosphere=params.use_variable_atmosphere,
        )
        return results
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Simulation processing error: {str(exc)}")


@app.post("/api/simulate/monte-carlo")
async def run_monte_carlo(params: MonteCarloRequest) -> Dict[str, Any]:
    """
    Executes N Monte Carlo simulations with Gaussian dispersion applied to v0 and angle.
    Returns impact point scatter array and statistical metrics (mean, std dev, 95% CI).
    """
    try:
        results = await asyncio.to_thread(
            simulate_monte_carlo,
            v0=params.v0,
            angle_deg=params.angle_deg,
            mass=params.mass,
            k=params.k,
            wind_x=params.wind_x,
            wind_y=params.wind_y,
            g=params.g,
            dt=params.dt,
            use_variable_atmosphere=params.use_variable_atmosphere,
            num_simulations=params.num_simulations,
            v0_std_dev=params.v0_std_dev,
            angle_std_dev=params.angle_std_dev,
        )
        return results
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Monte Carlo simulation error: {str(exc)}")


@app.post("/api/export/csv")
async def export_csv(params: CSVExportRequest) -> Response:
    """
    Runs simulation and returns a downloadable CSV file containing:
    time, x, y, vx, vy, kinetic_energy, potential_energy, total_energy.
    """
    try:
        sim_results = await asyncio.to_thread(
            simulate_projectile,
            v0=params.v0,
            angle_deg=params.angle_deg,
            mass=params.mass,
            k=params.k,
            wind_x=params.wind_x,
            wind_y=params.wind_y,
            g=params.g,
            dt=params.dt,
            use_variable_atmosphere=params.use_variable_atmosphere,
        )

        selected_method = params.method.lower().strip()
        if selected_method not in ["rk4", "euler", "ideal"]:
            selected_method = "rk4"

        points = sim_results["trajectories"][selected_method]["points"]
        csv_content = await asyncio.to_thread(generate_trajectory_csv, points)

        filename = f"trajectory_{selected_method}_{int(params.v0)}ms_{int(params.angle_deg)}deg.csv"

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache",
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"CSV export error: {str(exc)}")


# Mount frontend directory so running 'python backend/main.py' serves both Web Dashboard and API on http://localhost:8000
frontend_path = PROJECT_ROOT / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True, app_dir=str(PROJECT_ROOT))
