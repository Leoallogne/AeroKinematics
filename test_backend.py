"""
Automated test script for physics simulation, Monte Carlo dispersion,
CSV export, and FastAPI endpoints.
"""
from backend.physics import simulate_projectile, simulate_monte_carlo
from backend.main import app
from fastapi.testclient import TestClient


def test_physics_simulation():
    # 1. Base simulation test
    res = simulate_projectile(
        v0=50.0,
        angle_deg=45.0,
        mass=1.0,
        k=0.02,
        wind_x=-5.0,
        wind_y=1.0,
        g=9.81,
        dt=0.01,
        use_variable_atmosphere=False,
    )
    assert "parameters" in res
    assert "trajectories" in res
    trajectories = res["trajectories"]

    for key in ["ideal", "euler", "rk4"]:
        assert key in trajectories, f"Missing trajectory model: {key}"
        traj = trajectories[key]
        points = traj["points"]
        assert len(points) > 1, f"{key} has insufficient points"
        # Ground impact test
        last_pt = points[-1]
        assert last_pt["y"] == 0.0, f"Last point y should be exactly 0.0, got {last_pt['y']}"
        assert last_pt["time"] > 0

    # 2. Variable atmosphere test: for high altitude launch, density decay reduces drag, increasing range
    res_const = simulate_projectile(
        v0=800.0, angle_deg=60.0, mass=50.0, k=0.05, wind_x=0.0, wind_y=0.0, g=9.81, dt=0.05, use_variable_atmosphere=False
    )
    res_var = simulate_projectile(
        v0=800.0, angle_deg=60.0, mass=50.0, k=0.05, wind_x=0.0, wind_y=0.0, g=9.81, dt=0.05, use_variable_atmosphere=True
    )
    range_const = res_const["trajectories"]["rk4"]["summary"]["max_range"]
    range_var = res_var["trajectories"]["rk4"]["summary"]["max_range"]

    print(f"High altitude RK4 range (Constant atm): {range_const:.2f} m | (Variable atm): {range_var:.2f} m")
    assert range_var > range_const, "Variable atmosphere with barometric density decay should increase high-altitude range"

    # 3. Direct Monte Carlo logic test
    mc_res = simulate_monte_carlo(
        v0=100.0,
        angle_deg=45.0,
        mass=2.0,
        k=0.01,
        wind_x=0.0,
        wind_y=0.0,
        g=9.81,
        dt=0.02,
        use_variable_atmosphere=False,
        num_simulations=60,
        v0_std_dev=3.0,
        angle_std_dev=1.5,
    )
    assert mc_res["num_simulations"] == 60
    assert len(mc_res["impact_points"]) == 60
    assert "mean_range" in mc_res["summary"]
    assert "std_dev_range" in mc_res["summary"]
    assert mc_res["summary"]["std_dev_range"] > 0.0

    print("[SUCCESS] All physics simulation, variable atmosphere & Monte Carlo logic tests passed.")


def test_api_endpoints():
    client = TestClient(app)

    # 1. Root & Health
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "online"

    # 2. Standard Simulation Endpoint
    payload = {
        "v0": 100.0,
        "angle_deg": 45.0,
        "mass": 2.0,
        "k": 0.01,
        "wind_x": -3.0,
        "wind_y": 0.0,
        "g": 9.81,
        "dt": 0.01,
        "use_variable_atmosphere": True,
    }
    response = client.post("/api/simulate", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["parameters"]["use_variable_atmosphere"] is True
    assert "trajectories" in data

    # 3. Monte Carlo Endpoint (Valid 50-500 runs)
    mc_payload = {
        **payload,
        "num_simulations": 80,
        "v0_std_dev": 2.5,
        "angle_std_dev": 1.0,
    }
    res_mc = client.post("/api/simulate/monte-carlo", json=mc_payload)
    assert res_mc.status_code == 200, f"Expected 200, got {res_mc.status_code}: {res_mc.text}"
    mc_data = res_mc.json()
    assert mc_data["num_simulations"] == 80
    assert len(mc_data["impact_points"]) == 80
    assert "mean_range" in mc_data["summary"]
    assert "ci_95_mean_margin" in mc_data["summary"]

    # 4. Monte Carlo Validation (num_simulations < 50 -> HTTP 422)
    mc_invalid = {**mc_payload, "num_simulations": 20}
    res_mc_inv = client.post("/api/simulate/monte-carlo", json=mc_invalid)
    assert res_mc_inv.status_code == 422, f"Expected 422 for num_simulations=20, got {res_mc_inv.status_code}"

    # 5. CSV Export Endpoint
    csv_payload = {
        **payload,
        "method": "rk4",
    }
    res_csv = client.post("/api/export/csv", json=csv_payload)
    assert res_csv.status_code == 200, f"Expected 200, got {res_csv.status_code}"
    assert "text/csv" in res_csv.headers["content-type"]
    assert "attachment; filename=" in res_csv.headers["content-disposition"]

    csv_text = res_csv.text
    first_line = csv_text.splitlines()[0]
    expected_header = "time,x,y,vx,vy,kinetic_energy,potential_energy,total_energy"
    assert first_line == expected_header, f"Header mismatch: {first_line}"
    assert len(csv_text.splitlines()) > 50

    print("[SUCCESS] All FastAPI endpoints (simulate, monte-carlo, export/csv, 422 validation) passed.")


if __name__ == "__main__":
    test_physics_simulation()
    test_api_endpoints()
    print("ALL ADVANCED FEATURE TESTS PASSED SUCCESSFULLY!")
