"""
FastAPI Backend for 2D Projectile Motion Simulation.
Provides REST API endpoints with strict validation for projectile trajectory simulation.
"""

from typing import Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

from backend.physics import simulate_projectile


app = FastAPI(
    title="2D Projectile Motion Simulation API",
    description="Simulates projectile trajectories comparing Ideal, Euler, and RK4 integration methods.",
    version="1.1.0",
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
    v0: float = Field(..., gt=0.0, le=2000.0, description="Initial velocity in m/s (0 < v0 <= 2000)")
    angle_deg: float = Field(45.0, ge=0.0, le=90.0, description="Launch angle in degrees (0 <= angle <= 90)")
    mass: float = Field(..., gt=0.0, description="Projectile mass in kg (mass > 0)")
    k: float = Field(0.01, ge=0.0, description="Aerodynamic drag coefficient (k >= 0)")
    wind_x: float = Field(0.0, description="Wind speed along horizontal X axis (m/s)")
    wind_y: float = Field(0.0, description="Wind speed along vertical Y axis (m/s)")
    g: float = Field(9.81, gt=0.0, description="Gravitational acceleration in m/s^2 (g > 0)")
    dt: float = Field(0.01, gt=0.0, le=0.1, description="Simulation time step in seconds (0 < dt <= 0.1)")

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
            wind_y=params.wind_y,
            g=params.g,
            dt=params.dt,
        )
        return results
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Simulation processing error: {str(exc)}")


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
