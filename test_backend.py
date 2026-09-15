"""
Automated test script for physics simulation and FastAPI endpoint.
"""
import sys
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
    g = 9.81
    dt = 0.01

    res = simulate_projectile(v0=v0, angle_deg=angle_deg, mass=mass, k=k, wind_x=wind_x, g=g, dt=dt)

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

        # Check points structure
        first_pt = points[0]
        assert first_pt["time"] == 0.0
        assert first_pt["x"] == 0.0
        assert first_pt["y"] == 0.0
        for energy_field in ["Ek", "Ep", "Em"]:
            assert energy_field in first_pt, f"Missing {energy_field} in {key} points"

        # Check landing condition
        last_pt = points[-1]
        assert last_pt["y"] == 0.0, f"Last point y should be 0.0, got {last_pt['y']}"
        assert last_pt["time"] > 0

    # Physical checks:
    # 1. Ideal max height should be close to (v0*sin(45))^2 / (2*g)
    expected_ideal_h = ((v0 * math.sin(math.radians(45))) ** 2) / (2 * g)
    actual_ideal_h = trajectories["ideal"]["summary"]["max_height"]
    assert abs(actual_ideal_h - expected_ideal_h) < 0.2, f"Ideal height mismatch: {actual_ideal_h} vs {expected_ideal_h}"

    # 2. Drag should reduce range compared to ideal (especially with headwind wind_x = -5)
    ideal_range = trajectories["ideal"]["summary"]["max_range"]
    euler_range = trajectories["euler"]["summary"]["max_range"]
    rk4_range = trajectories["rk4"]["summary"]["max_range"]

    print(f"Ideal range: {ideal_range:.2f} m | Euler range: {euler_range:.2f} m | RK4 range: {rk4_range:.2f} m")
    assert euler_range < ideal_range, "Euler range with drag should be less than ideal range"
    assert rk4_range < ideal_range, "RK4 range with drag should be less than ideal range"

    # 3. Ideal total energy should be conserved (Em initial == Em final)
    em_start = trajectories["ideal"]["points"][0]["Em"]
    em_end = trajectories["ideal"]["points"][-1]["Em"]
    assert abs(em_start - em_end) < 0.1, f"Ideal Em not conserved: start={em_start}, end={em_end}"

    # 4. Drag trajectories should lose mechanical energy over time
    rk4_pts = trajectories["rk4"]["points"]
    assert rk4_pts[-1]["Em"] < rk4_pts[0]["Em"], "RK4 trajectory should lose energy due to drag"

    print("[SUCCESS] All physics simulation logic tests passed.")


def test_api_endpoint():
    client = TestClient(app)

    # Test root endpoint
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "online"

    # Test simulate endpoint
    payload = {
        "v0": 60.0,
        "angle_deg": 30.0,
        "mass": 2.5,
        "k": 0.015,
        "wind_x": 3.0,
        "g": 9.81,
        "dt": 0.01
    }
    response = client.post("/api/simulate", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "parameters" in data
    assert "trajectories" in data
    assert data["parameters"]["v0"] == 60.0
    assert "ideal" in data["trajectories"]
    assert "euler" in data["trajectories"]
    assert "rk4" in data["trajectories"]

    print("[SUCCESS] FastAPI test client endpoint verification passed.")


if __name__ == "__main__":
    test_physics_simulation()
    test_api_endpoint()
    print("ALL TESTS PASSED SUCCESSFULLY!")
