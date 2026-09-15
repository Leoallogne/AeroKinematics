"""
FastAPI Backend for 2D Projectile Motion Simulation.
Provides REST API endpoints to simulate projectile trajectories under ideal and drag conditions.
"""

from typing import Dict, Any, List, Optional
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.physics import simulate_projectile


app = FastAPI(
    title="2D Projectile Motion Simulation API",
    description="Simulates projectile trajectories comparing Ideal, Euler, and RK4 integration methods.",
    version="1.0.0",
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
    v0: float = Field(50.0, gt=0, description="Initial velocity (m/s)")
    angle_deg: float = Field(45.0, ge=0.0, le=90.0, description="Launch angle in degrees (0 - 90)")
    mass: float = Field(1.0, gt=0, description="Projectile mass (kg)")
    k: float = Field(0.01, ge=0, description="Aerodynamic drag coefficient (kg/m)")
    wind_x: float = Field(0.0, description="Wind speed along horizontal axis (m/s)")
    g: float = Field(9.81, gt=0, description="Gravitational acceleration (m/s^2)")
    dt: float = Field(0.01, gt=0.0, le=0.5, description="Simulation time step (s)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "v0": 50.0,
                "angle_deg": 45.0,
                "mass": 1.0,
                "k": 0.01,
                "wind_x": -5.0,
                "g": 9.81,
                "dt": 0.01,
            }
        }
    }


@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "2D Projectile Motion Simulation API",
        "docs_url": "/docs",
    }


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/simulate")
def run_simulation(params: SimulationRequest) -> Dict[str, Any]:
    """
    Executes the 2D projectile motion simulation comparing:
    - Ideal (Analytical, no drag)
    - Euler numerical integration (Drag + Wind)
    - RK4 numerical integration (Drag + Wind)

    Returns trajectories, summary metrics, and energy logs for each model.
    """
    try:
        results = simulate_projectile(
            v0=params.v0,
            angle_deg=params.angle_deg,
            mass=params.mass,
            k=params.k,
            wind_x=params.wind_x,
            g=params.g,
            dt=params.dt,
        )
        return results
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(exc)}")


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
