"""
Automated test script for physics simulation and FastAPI endpoint.
"""
import math
from backend.physics import simulate_projectile
from backend.main import app
from fastapi.testclient import TestClient

def test_physics_simulation():
    v0 = 50.0
    angle_deg = 45.0
    mass = 1.0
    k = 0.02
    wind_x = -5.0
    wind_y = 1.0
    g = 9.81
    dt = 0.01

    res = simulate_projectile(v0=v0, angle_deg=angle_deg, mass=mass, k=k, wind_x=wind_x, wind_y=wind_y, g=g, dt=dt)

    assert "parameters" in res
    assert "trajectories" in res
    trajectories = res["trajectories"]

    for key in ["ideal", "euler", "rk4"]:
        assert key in trajectories, f"Missing trajectory model: {key}"
        traj = trajectories[key]
        assert "summary" in traj
        assert "points" in traj
        summary = traj["summary"]
        points = traj["points"]

        assert len(points) > 1, f"{key} has insufficient points"
        assert "max_height" in summary
        assert "max_range" in summary
        assert "flight_time" in summary
        assert "impact_velocity" in summary

        first_pt = points[0]
        assert first_pt["time"] == 0.0
        assert first_pt["x"] == 0.0
        assert first_pt["y"] == 0.0
        for energy_field in ["Ek", "Ep", "Em"]:
            assert energy_field in first_pt, f"Missing {energy_field} in {key} points"

        # Exact ground impact test (y = 0.0)
        last_pt = points[-1]
        assert last_pt["y"] == 0.0, f"Last point y should be exactly 0.0, got {last_pt['y']}"
        assert last_pt["time"] > 0

    print("[SUCCESS] Refactored physics simulation logic & landing interpolation tests passed.")


def test_api_endpoint():
    client = TestClient(app)

    # Test root endpoint
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "online"

    # Test valid simulate endpoint
    payload = {
        "v0": 60.0,
        "angle_deg": 30.0,
        "mass": 2.5,
        "k": 0.015,
        "wind_x": 3.0,
        "wind_y": 0.0,
        "g": 9.81,
        "dt": 0.01
    }
    response = client.post("/api/simulate", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "parameters" in data
    assert "trajectories" in data

    # Test invalid payload (mass <= 0 -> HTTP 422)
    invalid_payload = {
        "v0": 50.0,
        "angle_deg": 45.0,
        "mass": 0.0,  # Invalid: mass must be > 0
        "k": 0.01,
        "wind_x": 0.0,
        "g": 9.81,
        "dt": 0.01
    }
    res_invalid = client.post("/api/simulate", json=invalid_payload)
    assert res_invalid.status_code == 422, f"Expected 422 for mass=0, got {res_invalid.status_code}"

    print("[SUCCESS] FastAPI test client endpoint & Pydantic 422 validation verification passed.")


if __name__ == "__main__":
    test_physics_simulation()
    test_api_endpoint()
    print("ALL TESTS PASSED SUCCESSFULLY!")
