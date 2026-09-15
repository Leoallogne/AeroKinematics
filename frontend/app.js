/**
 * 2D Projectile Physics Lab & Solver Engine - Frontend Application
 * Handles:
 * 1. API Communication with FastAPI backend (http://localhost:8000/api/simulate)
 * 2. Dynamic HTML5 Canvas rendering (renderCanvas) with multi-model trail lines,
 *    axis scaling, grid, and frame-by-frame projectile animation.
 * 3. Real-time Chart.js Energy breakdown (renderEnergyChart) synchronized with
 *    the projectile's instantaneous position.
 * 4. Export CSV functionality for trajectory points.
 */

(() => {
  // ==========================================
  // 1. DOM REFERENCES & INITIAL STATE
  // ==========================================
  const inputs = {
    v0_num: document.getElementById('v0_num'),
    v0_range: document.getElementById('v0_range'),
    angle_num: document.getElementById('angle_num'),
    angle_range: document.getElementById('angle_range'),
    mass_num: document.getElementById('mass_num'),
    mass_range: document.getElementById('mass_range'),
    k_num: document.getElementById('k_num'),
    k_range: document.getElementById('k_range'),
    wind_num: document.getElementById('wind_num'),
    wind_range: document.getElementById('wind_range'),
  };

  const toggles = {
    ideal: document.getElementById('toggleIdeal'),
    euler: document.getElementById('toggleEuler'),
    rk4: document.getElementById('toggleRK4'),
  };

  const buttons = {
    launch: document.getElementById('btnLaunch'),
    reset: document.getElementById('btnReset'),
    exportCsv: document.getElementById('btnExport'),
    replay: document.getElementById('btnReplay'),
  };

  const metrics = {
    maxHeight: document.getElementById('metricMaxHeight'),
    subHeightIdeal: document.getElementById('subHeightIdeal'),
    subHeightEuler: document.getElementById('subHeightEuler'),
    maxRange: document.getElementById('metricMaxRange'),
    subRangeIdeal: document.getElementById('subRangeIdeal'),
    subRangeEuler: document.getElementById('subRangeEuler'),
    flightTime: document.getElementById('metricFlightTime'),
    subTimeIdeal: document.getElementById('subTimeIdeal'),
    subTimeEuler: document.getElementById('subTimeEuler'),
    energyLoss: document.getElementById('metricEnergyLoss'),
    subEmInitial: document.getElementById('subEmInitial'),
    subImpactV: document.getElementById('subImpactV'),
  };

  const canvas = document.getElementById('trajectoryCanvas');
  const ctx = canvas.getContext('2d');
  const canvasTooltip = document.getElementById('canvasTooltip');
  const windIndicatorTag = document.getElementById('windIndicatorTag');
  const scaleInfo = document.getElementById('scaleInfo');
  const playbackSpeed = document.getElementById('playbackSpeed');
  const animStateDot = document.getElementById('animStateDot');
  const chartViewMode = document.getElementById('chartViewMode');
  const backendStatusDot = document.getElementById('backendStatusDot');
  const backendStatusText = document.getElementById('backendStatusText');

  // Simulation State
  let simulationData = null;
  let energyChart = null;
  let animationFrameId = null;
  let animProgress = 1.0; // 0.0 to 1.0
  let isAnimating = false;
  let animStartTime = null;
  let debounceTimer = null;

  // Coordinate Bounds & Transform Matrix
  const transform = {
    xMin: 0,
    xMax: 100,
    yMin: 0,
    yMax: 50,
    scaleX: 1,
    scaleY: 1,
    padLeft: 55,
    padRight: 35,
    padTop: 30,
    padBottom: 40,
    plotWidth: 0,
    plotHeight: 0,
  };

  // ==========================================
  // 2. INPUT SYNCHRONIZATION & EVENT BINDING
  // ==========================================
  function setupInputSync(numEl, rangeEl) {
    numEl.addEventListener('input', () => {
      rangeEl.value = numEl.value;
      onInputChange();
    });
    rangeEl.addEventListener('input', () => {
      numEl.value = rangeEl.value;
      onInputChange();
    });
  }

  setupInputSync(inputs.v0_num, inputs.v0_range);
  setupInputSync(inputs.angle_num, inputs.angle_range);
  setupInputSync(inputs.mass_num, inputs.mass_range);
  setupInputSync(inputs.k_num, inputs.k_range);
  setupInputSync(inputs.wind_num, inputs.wind_range);

  function updateWindBadge() {
    const w = parseFloat(inputs.wind_num.value) || 0;
    if (w === 0) {
      windIndicatorTag.textContent = 'Wind: Calm (0 m/s)';
      windIndicatorTag.className = 'text-[11px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/60 font-mono';
    } else if (w > 0) {
      windIndicatorTag.textContent = `Wind: +${w} m/s Tailwind →`;
      windIndicatorTag.className = 'text-[11px] px-2 py-0.5 rounded-full bg-emerald-950/60 text-emerald-300 border border-emerald-700/50 font-mono';
    } else {
      windIndicatorTag.textContent = `Wind: ${w} m/s Headwind ←`;
      windIndicatorTag.className = 'text-[11px] px-2 py-0.5 rounded-full bg-rose-950/60 text-rose-300 border border-rose-700/50 font-mono';
    }
  }

  // Trigger simulation on input change (debounced 180ms for responsive UI)
  function onInputChange() {
    updateWindBadge();
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      fetchSimulationData();
    }, 180);
  }

  // ==========================================
  // 3. API COMMUNICATION (POST /api/simulate)
  // ==========================================
  async function fetchSimulationData() {
    const payload = {
      v0: parseFloat(inputs.v0_num.value) || 50.0,
      angle_deg: parseFloat(inputs.angle_num.value) || 45.0,
      mass: parseFloat(inputs.mass_num.value) || 1.0,
      k: parseFloat(inputs.k_num.value) || 0.01,
      wind_x: parseFloat(inputs.wind_num.value) || 0.0,
      g: 9.81,
      dt: 0.01,
    };

    try {
      const response = await fetch('http://localhost:8000/api/simulate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      simulationData = data;

      backendStatusDot.className = 'w-2 h-2 rounded-full bg-emerald-400 pulse-active';
      backendStatusText.textContent = 'FastAPI Engine Connected';

      updateMetrics();
      startAnimation();
    } catch (error) {
      console.warn('Backend API request failed, activating client fallback:', error);
      simulationData = clientSideFallback(payload);
      backendStatusDot.className = 'w-2 h-2 rounded-full bg-amber-400';
      backendStatusText.textContent = 'Client Physics Solver Active';

      updateMetrics();
      startAnimation();
    }
  }

  // Client-side fallback solver in case backend is offline
  function clientSideFallback(p) {
    const angleRad = (p.angle_deg * Math.PI) / 180.0;
    const vx0 = p.v0 * Math.cos(angleRad);
    const vy0 = p.v0 * Math.sin(angleRad);
    const dt = p.dt;

    function pt(t, x, y, vx, vy) {
      const cy = Math.max(0, y);
      const v2 = vx * vx + vy * vy;
      const Ek = 0.5 * p.mass * v2;
      const Ep = p.mass * p.g * cy;
      return {
        time: parseFloat(t.toFixed(4)),
        x: parseFloat(x.toFixed(4)),
        y: parseFloat(cy.toFixed(4)),
        vx: parseFloat(vx.toFixed(4)),
        vy: parseFloat(vy.toFixed(4)),
        Ek: parseFloat(Ek.toFixed(4)),
        Ep: parseFloat(Ep.toFixed(4)),
        Em: parseFloat((Ek + Ep).toFixed(4)),
      };
    }

    // 1. Ideal
    const idealPts = [];
    const tFlight = vy0 > 0 ? (2 * vy0) / p.g : 0;
    let t = 0;
    while (t < tFlight) {
      idealPts.push(pt(t, vx0 * t, vy0 * t - 0.5 * p.g * t * t, vx0, vy0 - p.g * t));
      t += dt;
    }
    idealPts.push(pt(tFlight, vx0 * tFlight, 0, vx0, vy0 - p.g * tFlight));

    // 2. Euler
    const eulerPts = [pt(0, 0, 0, vx0, vy0)];
    let [et, ex, ey, evx, evy] = [0, 0, 0, vx0, vy0];
    for (let i = 0; i < 40000; i++) {
      const vrx = evx - p.wind_x;
      const vr = Math.hypot(vrx, evy);
      const ax = -(p.k / p.mass) * vr * vrx;
      const ay = -p.g - (p.k / p.mass) * vr * evy;
      const nx = ex + evx * dt;
      const ny = ey + evy * dt;
      const nvx = evx + ax * dt;
      const nvy = evy + ay * dt;
      const nt = et + dt;
      if (ny < 0) {
        const f = -ey / (ny - ey);
        eulerPts.push(pt(et + f * dt, ex + f * (nx - ex), 0, evx + f * (nvx - evx), evy + f * (nvy - evy)));
        break;
      }
      eulerPts.push(pt(nt, nx, ny, nvx, nvy));
      [et, ex, ey, evx, evy] = [nt, nx, ny, nvx, nvy];
    }

    // 3. RK4
    const rk4Pts = [pt(0, 0, 0, vx0, vy0)];
    let state = [0, 0, vx0, vy0];
    let rt = 0;
    const deriv = (s) => {
      const vrx = s[2] - p.wind_x;
      const vr = Math.hypot(vrx, s[3]);
      return [s[2], s[3], -(p.k / p.mass) * vr * vrx, -p.g - (p.k / p.mass) * vr * s[3]];
    };

    for (let i = 0; i < 40000; i++) {
      const k1 = deriv(state);
      const s2 = state.map((v, idx) => v + 0.5 * dt * k1[idx]);
      const k2 = deriv(s2);
      const s3 = state.map((v, idx) => v + 0.5 * dt * k2[idx]);
      const k3 = deriv(s3);
      const s4 = state.map((v, idx) => v + dt * k3[idx]);
      const k4 = deriv(s4);
      const nxt = state.map((v, idx) => v + (dt / 6.0) * (k1[idx] + 2 * k2[idx] + 2 * k3[idx] + k4[idx]));
      const nt = rt + dt;
      if (nxt[1] < 0) {
        const f = -state[1] / (nxt[1] - state[1]);
        rk4Pts.push(pt(rt + f * dt, state[0] + f * (nxt[0] - state[0]), 0, state[2] + f * (nxt[2] - state[2]), state[3] + f * (nxt[3] - state[3])));
        break;
      }
      rk4Pts.push(pt(nt, nxt[0], nxt[1], nxt[2], nxt[3]));
      state = nxt;
      rt = nt;
    }

    const summ = (pts) => {
      const maxH = Math.max(...pts.map((p) => p.y));
      const last = pts[pts.length - 1];
      return {
        max_height: parseFloat(maxH.toFixed(4)),
        max_range: parseFloat(last.x.toFixed(4)),
        flight_time: parseFloat(last.time.toFixed(4)),
        impact_velocity: parseFloat(Math.hypot(last.vx, last.vy).toFixed(4)),
      };
    };

    return {
      parameters: p,
      trajectories: {
        ideal: { summary: summ(idealPts), points: idealPts },
        euler: { summary: summ(eulerPts), points: eulerPts },
        rk4: { summary: summ(rk4Pts), points: rk4Pts },
      },
    };
  }

  // ==========================================
  // 4. METRIC CARDS UPDATER
  // ==========================================
  function updateMetrics() {
    if (!simulationData) return;
    const { ideal, euler, rk4 } = simulationData.trajectories;
    const primary = toggles.rk4.checked ? rk4 : (toggles.euler.checked ? euler : ideal);
    const summary = primary.summary;

    metrics.maxHeight.textContent = summary.max_height.toFixed(1);
    metrics.maxRange.textContent = summary.max_range.toFixed(1);
    metrics.flightTime.textContent = summary.flight_time.toFixed(2);

    metrics.subHeightIdeal.textContent = `${ideal.summary.max_height.toFixed(1)}m`;
    metrics.subHeightEuler.textContent = `${euler.summary.max_height.toFixed(1)}m`;
    metrics.subRangeIdeal.textContent = `${ideal.summary.max_range.toFixed(1)}m`;
    metrics.subRangeEuler.textContent = `${euler.summary.max_range.toFixed(1)}m`;
    metrics.subTimeIdeal.textContent = `${ideal.summary.flight_time.toFixed(2)}s`;
    metrics.subTimeEuler.textContent = `${euler.summary.flight_time.toFixed(2)}s`;

    const em0 = primary.points[0].Em;
    const emEnd = primary.points[primary.points.length - 1].Em;
    const lossPct = em0 > 0 ? Math.max(0, ((em0 - emEnd) / em0) * 100) : 0;
    metrics.energyLoss.textContent = lossPct.toFixed(1);

    metrics.subEmInitial.textContent = `${Math.round(em0)} J`;
    metrics.subImpactV.textContent = `${summary.impact_velocity.toFixed(1)} m/s`;
  }

  // ==========================================
  // 5. HTML5 CANVAS RENDERER (renderCanvas)
  // ==========================================
  function resizeCanvas() {
    const container = canvas.parentElement;
    const rect = container.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.resetTransform();
    ctx.scale(dpr, dpr);
    renderCanvas(animProgress);
  }

  function updateDynamicScale() {
    if (!simulationData) return;
    const { ideal, euler, rk4 } = simulationData.trajectories;

    let maxX = 10;
    let minX = 0;
    let maxY = 10;

    const activeList = [];
    if (toggles.ideal.checked) activeList.push(ideal);
    if (toggles.euler.checked) activeList.push(euler);
    if (toggles.rk4.checked) activeList.push(rk4);
    if (activeList.length === 0) activeList.push(rk4);

    activeList.forEach((traj) => {
      maxX = Math.max(maxX, traj.summary.max_range);
      maxY = Math.max(maxY, traj.summary.max_height);
      traj.points.forEach((p) => {
        if (p.x < minX) minX = p.x;
      });
    });

    // 15% visual padding headroom
    maxX = Math.ceil((maxX * 1.15) / 10) * 10;
    minX = Math.min(0, Math.floor((minX * 1.15) / 10) * 10);
    maxY = Math.ceil((maxY * 1.25) / 5) * 5;

    const w = canvas.width / (window.devicePixelRatio || 1);
    const h = canvas.height / (window.devicePixelRatio || 1);

    transform.xMin = minX;
    transform.xMax = Math.max(minX + 10, maxX);
    transform.yMin = 0;
    transform.yMax = Math.max(10, maxY);
    transform.plotWidth = w - transform.padLeft - transform.padRight;
    transform.plotHeight = h - transform.padTop - transform.padBottom;
    transform.scaleX = transform.plotWidth / (transform.xMax - transform.xMin);
    transform.scaleY = transform.plotHeight / (transform.yMax - transform.yMin);

    scaleInfo.textContent = `X: [${transform.xMin}m, ${transform.xMax}m] | Y: [0m, ${transform.yMax}m]`;
  }

  function toCanvasCoords(x, y) {
    const cx = transform.padLeft + (x - transform.xMin) * transform.scaleX;
    const cy = transform.padTop + transform.plotHeight - (y - transform.yMin) * transform.scaleY;
    return [cx, cy];
  }

  function toPhysicsCoords(cx, cy) {
    const x = transform.xMin + (cx - transform.padLeft) / transform.scaleX;
    const y = transform.yMin + (transform.padTop + transform.plotHeight - cy) / transform.scaleY;
    return [x, y];
  }

  function drawCartesianAxes() {
    const w = canvas.width / (window.devicePixelRatio || 1);
    const h = canvas.height / (window.devicePixelRatio || 1);

    ctx.clearRect(0, 0, w, h);

    // Dark gradient background
    const bgGrad = ctx.createLinearGradient(0, 0, 0, h);
    bgGrad.addColorStop(0, '#060a12');
    bgGrad.addColorStop(1, '#0c1424');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, w, h);

    // Compute pleasant round intervals
    const calcInterval = (range) => {
      const raw = range / 8;
      const mag = Math.pow(10, Math.floor(Math.log10(raw)));
      const norm = raw / mag;
      if (norm < 1.5) return 1 * mag;
      if (norm < 3.5) return 2 * mag;
      if (norm < 7.5) return 5 * mag;
      return 10 * mag;
    };

    const xStep = Math.max(1, calcInterval(transform.xMax - transform.xMin));
    const yStep = Math.max(1, calcInterval(transform.yMax - transform.yMin));

    // Vertical grid lines & X-axis labels
    const startX = Math.floor(transform.xMin / xStep) * xStep;
    for (let x = startX; x <= transform.xMax; x += xStep) {
      const [cx] = toCanvasCoords(x, 0);
      if (cx < transform.padLeft - 2 || cx > transform.padLeft + transform.plotWidth + 2) continue;

      ctx.strokeStyle = x === 0 ? 'rgba(71, 85, 105, 0.7)' : 'rgba(30, 41, 59, 0.4)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(cx, transform.padTop);
      ctx.lineTo(cx, transform.padTop + transform.plotHeight);
      ctx.stroke();

      ctx.fillStyle = '#64748b';
      ctx.font = '10px JetBrains Mono, monospace';
      ctx.textAlign = 'center';
      ctx.fillText(`${Math.round(x)}m`, cx, transform.padTop + transform.plotHeight + 16);
    }

    // Horizontal grid lines & Y-axis labels
    for (let y = 0; y <= transform.yMax; y += yStep) {
      const [, cy] = toCanvasCoords(0, y);
      if (cy > transform.padTop + transform.plotHeight + 2 || cy < transform.padTop - 2) continue;

      ctx.strokeStyle = y === 0 ? 'rgba(56, 189, 248, 0.6)' : 'rgba(30, 41, 59, 0.4)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(transform.padLeft, cy);
      ctx.lineTo(transform.padLeft + transform.plotWidth, cy);
      ctx.stroke();

      ctx.fillStyle = '#64748b';
      ctx.font = '10px JetBrains Mono, monospace';
      ctx.textAlign = 'right';
      ctx.fillText(`${Math.round(y)}m`, transform.padLeft - 8, cy + 3.5);
    }

    // Ground Baseline (y = 0)
    const [gx1, gy] = toCanvasCoords(transform.xMin, 0);
    const [gx2] = toCanvasCoords(transform.xMax, 0);
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(gx1, gy);
    ctx.lineTo(gx2, gy);
    ctx.stroke();

    // Ground Hatching
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.2)';
    ctx.lineWidth = 1;
    for (let gx = gx1; gx < gx2; gx += 14) {
      ctx.beginPath();
      ctx.moveTo(gx, gy);
      ctx.lineTo(gx - 6, gy + 8);
      ctx.stroke();
    }

    // Origin Launch Point (0,0)
    const [ox, oy] = toCanvasCoords(0, 0);
    ctx.save();
    ctx.fillStyle = '#38bdf8';
    ctx.shadowColor = '#38bdf8';
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.arc(ox, oy, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function drawTrail(points, style, progress = 1.0) {
    if (!points || points.length === 0) return;
    const count = Math.max(1, Math.floor(points.length * progress));
    const active = points.slice(0, count);

    ctx.save();
    ctx.strokeStyle = style.color;
    ctx.lineWidth = style.lineWidth;
    if (style.dashed) ctx.setLineDash(style.dashed);
    else ctx.setLineDash([]);

    if (style.glow) {
      ctx.shadowColor = style.color;
      ctx.shadowBlur = style.glow;
    }

    ctx.beginPath();
    active.forEach((p, idx) => {
      const [cx, cy] = toCanvasCoords(p.x, p.y);
      if (idx === 0) ctx.moveTo(cx, cy);
      else ctx.lineTo(cx, cy);
    });
    ctx.stroke();
    ctx.restore();

    // Peak & Impact Annotations when completed
    if (progress >= 0.99 && active.length > 2) {
      let peak = active[0];
      active.forEach((p) => {
        if (p.y > peak.y) peak = p;
      });

      if (peak.y > 0.5) {
        const [px, py] = toCanvasCoords(peak.x, peak.y);
        ctx.save();
        ctx.fillStyle = style.color;
        ctx.beginPath();
        ctx.arc(px, py, 3, 0, Math.PI * 2);
        ctx.fill();
        ctx.font = '10px JetBrains Mono, monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`${peak.y.toFixed(1)}m`, px, py - 8);
        ctx.restore();
      }

      const impact = active[active.length - 1];
      const [ix, iy] = toCanvasCoords(impact.x, impact.y);
      ctx.save();
      ctx.fillStyle = style.color;
      ctx.beginPath();
      ctx.arc(ix, iy, 3.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.font = '10px JetBrains Mono, monospace';
      ctx.textAlign = 'center';
      ctx.fillText(`${impact.x.toFixed(1)}m`, ix, iy + 14);
      ctx.restore();
    }
  }

  function drawProjectileBall(rk4Points, progress) {
    if (!rk4Points || rk4Points.length === 0) return;
    const targetIdx = Math.min(rk4Points.length - 1, Math.floor((rk4Points.length - 1) * progress));
    const head = rk4Points[targetIdx];
    const [hx, hy] = toCanvasCoords(head.x, head.y);

    ctx.save();
    // Glowing outer halo
    ctx.fillStyle = 'rgba(6, 182, 212, 0.25)';
    ctx.beginPath();
    ctx.arc(hx, hy, 9, 0, Math.PI * 2);
    ctx.fill();

    // Projectile ball core
    ctx.fillStyle = '#22d3ee';
    ctx.shadowColor = '#06b6d4';
    ctx.shadowBlur = 14;
    ctx.beginPath();
    ctx.arc(hx, hy, 4.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  /**
   * Main Canvas Render Function
   */
  function renderCanvas(progress = 1.0) {
    if (!simulationData) return;
    updateDynamicScale();
    drawCartesianAxes();

    const { ideal, euler, rk4 } = simulationData.trajectories;

    // 1. Draw Ideal Trail (Slate dashed)
    if (toggles.ideal.checked) {
      drawTrail(ideal.points, {
        color: '#94a3b8',
        lineWidth: 2,
        dashed: [6, 6],
        glow: 0,
      }, progress);
    }

    // 2. Draw Euler Trail (Yellow solid)
    if (toggles.euler.checked) {
      drawTrail(euler.points, {
        color: '#eab308',
        lineWidth: 2.5,
        dashed: null,
        glow: 6,
      }, progress);
    }

    // 3. Draw RK4 Trail (Cyan glow solid)
    if (toggles.rk4.checked) {
      drawTrail(rk4.points, {
        color: '#06b6d4',
        lineWidth: 3,
        dashed: null,
        glow: 12,
      }, progress);

      // Animate the projectile ball frame-by-frame along RK4
      drawProjectileBall(rk4.points, progress);
    }
  }

  // ==========================================
  // 6. CHART.JS ENERGY BREAKDOWN (renderEnergyChart)
  // ==========================================
  function initEnergyChart() {
    const chartCanvas = document.getElementById('energyChart');
    const chartCtx = chartCanvas.getContext('2d');

    energyChart = new Chart(chartCtx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Total Em (RK4)',
            data: [],
            borderColor: '#818cf8',
            backgroundColor: 'rgba(129, 140, 248, 0.08)',
            borderWidth: 2.5,
            tension: 0.15,
            pointRadius: 0,
            fill: false,
          },
          {
            label: 'Kinetic Ek (RK4)',
            data: [],
            borderColor: '#06b6d4',
            backgroundColor: 'transparent',
            borderWidth: 2,
            tension: 0.15,
            pointRadius: 0,
          },
          {
            label: 'Potential Ep (RK4)',
            data: [],
            borderColor: '#f59e0b',
            backgroundColor: 'transparent',
            borderWidth: 2,
            tension: 0.15,
            pointRadius: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false, // Turned off for smooth 60fps synchronous frame updates
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            position: 'top',
            labels: {
              boxWidth: 12,
              color: '#94a3b8',
              font: { family: 'JetBrains Mono', size: 11 },
            },
          },
          tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.94)',
            titleColor: '#e2e8f0',
            bodyColor: '#cbd5e1',
            borderColor: '#334155',
            borderWidth: 1,
            callbacks: {
              label: (item) => `${item.dataset.label}: ${item.parsed.y.toFixed(1)} J`,
            },
          },
        },
        scales: {
          x: {
            title: { display: true, text: 'Time (s)', color: '#64748b', font: { size: 10 } },
            grid: { color: 'rgba(30, 41, 59, 0.4)' },
            ticks: { color: '#64748b', maxTicksLimit: 10, font: { size: 10, family: 'JetBrains Mono' } },
          },
          y: {
            title: { display: true, text: 'Energy (Joules)', color: '#64748b', font: { size: 10 } },
            grid: { color: 'rgba(30, 41, 59, 0.4)' },
            ticks: { color: '#64748b', font: { size: 10, family: 'JetBrains Mono' } },
            min: 0,
          },
        },
      },
    });
  }

  /**
   * Updates Chart.js line chart synchronized with the projectile position
   */
  function renderEnergyChart(currentProgress = 1.0) {
    if (!simulationData || !energyChart) return;
    const { ideal, euler, rk4 } = simulationData.trajectories;
    const mode = chartViewMode.value;

    // Downsample for high-performance rendering across thousands of integration steps
    const sampleRate = Math.max(1, Math.floor(rk4.points.length / 80));
    const sample = (arr) => arr.filter((_, idx) => idx % sampleRate === 0 || idx === arr.length - 1);

    const sampledRK4 = sample(rk4.points);
    const fullTimeLabels = sampledRK4.map((p) => p.time.toFixed(2));

    // Current index based on projectile's animated progress
    const activeCount = Math.max(1, Math.floor(sampledRK4.length * currentProgress));

    if (mode === 'rk4_breakdown') {
      energyChart.data.labels = fullTimeLabels;
      energyChart.data.datasets = [
        {
          label: 'Total Em (RK4)',
          data: sampledRK4.map((p, idx) => (idx < activeCount ? p.Em : null)),
          borderColor: '#818cf8',
          borderWidth: 2.5,
          pointRadius: 0,
          spanGaps: false,
        },
        {
          label: 'Kinetic Ek (RK4)',
          data: sampledRK4.map((p, idx) => (idx < activeCount ? p.Ek : null)),
          borderColor: '#06b6d4',
          borderWidth: 2,
          pointRadius: 0,
          spanGaps: false,
        },
        {
          label: 'Potential Ep (RK4)',
          data: sampledRK4.map((p, idx) => (idx < activeCount ? p.Ep : null)),
          borderColor: '#f59e0b',
          borderWidth: 2,
          pointRadius: 0,
          spanGaps: false,
        },
      ];
    } else {
      // Comparison of Em across Ideal, Euler, and RK4
      const sampledIdeal = sample(ideal.points);
      const sampledEuler = sample(euler.points);
      const maxLen = Math.max(sampledIdeal.length, sampledEuler.length, sampledRK4.length);

      const labels = Array.from({ length: maxLen }, (_, i) => {
        const p = sampledRK4[i] || sampledEuler[i] || sampledIdeal[i];
        return p ? p.time.toFixed(2) : '';
      });

      energyChart.data.labels = labels;
      energyChart.data.datasets = [
        {
          label: 'Ideal Em (Conserved)',
          data: sampledIdeal.map((p, idx) => (idx < activeCount ? p.Em : null)),
          borderColor: '#94a3b8',
          borderDash: [5, 5],
          borderWidth: 2,
          pointRadius: 0,
        },
        {
          label: 'Euler Em',
          data: sampledEuler.map((p, idx) => (idx < activeCount ? p.Em : null)),
          borderColor: '#eab308',
          borderWidth: 2,
          pointRadius: 0,
        },
        {
          label: 'RK4 Em',
          data: sampledRK4.map((p, idx) => (idx < activeCount ? p.Em : null)),
          borderColor: '#06b6d4',
          borderWidth: 2.5,
          pointRadius: 0,
        },
      ];
    }

    // Update with 0 animation duration for instant 60fps sync
    energyChart.update('none');
  }

  // ==========================================
  // 7. ANIMATION CONTROLLER (requestAnimationFrame)
  // ==========================================
  function startAnimation() {
    if (animationFrameId) cancelAnimationFrame(animationFrameId);

    animProgress = 0.0;
    isAnimating = true;
    animStartTime = performance.now();
    animStateDot.className = 'w-2 h-2 rounded-full bg-cyan-400 animate-ping';

    const speed = parseFloat(playbackSpeed.value) || 4;
    const duration = 2400 / speed;

    function step(now) {
      const elapsed = now - animStartTime;
      animProgress = Math.min(1.0, elapsed / duration);

      // Render both canvas & chart in strict lockstep
      renderCanvas(animProgress);
      renderEnergyChart(animProgress);

      if (animProgress < 1.0) {
        animationFrameId = requestAnimationFrame(step);
      } else {
        isAnimating = false;
        animStateDot.className = 'w-2 h-2 rounded-full bg-cyan-400';
      }
    }

    animationFrameId = requestAnimationFrame(step);
  }

  // ==========================================
  // 8. EXPORT CSV FUNCTIONALITY
  // ==========================================
  function exportCSV() {
    if (!simulationData) {
      alert('Please run a simulation first before exporting.');
      return;
    }

    const { ideal, euler, rk4 } = simulationData.trajectories;
    const maxLen = Math.max(ideal.points.length, euler.points.length, rk4.points.length);

    const headers = [
      'step',
      'ideal_t(s)', 'ideal_x(m)', 'ideal_y(m)', 'ideal_vx(m/s)', 'ideal_vy(m/s)', 'ideal_Ek(J)', 'ideal_Ep(J)', 'ideal_Em(J)',
      'euler_t(s)', 'euler_x(m)', 'euler_y(m)', 'euler_vx(m/s)', 'euler_vy(m/s)', 'euler_Ek(J)', 'euler_Ep(J)', 'euler_Em(J)',
      'rk4_t(s)', 'rk4_x(m)', 'rk4_y(m)', 'rk4_vx(m/s)', 'rk4_vy(m/s)', 'rk4_Ek(J)', 'rk4_Ep(J)', 'rk4_Em(J)',
    ];

    const rows = [headers.join(',')];

    for (let i = 0; i < maxLen; i++) {
      const pi = ideal.points[i] || {};
      const pe = euler.points[i] || {};
      const pr = rk4.points[i] || {};

      const row = [
        i,
        pi.time ?? '', pi.x ?? '', pi.y ?? '', pi.vx ?? '', pi.vy ?? '', pi.Ek ?? '', pi.Ep ?? '', pi.Em ?? '',
        pe.time ?? '', pe.x ?? '', pe.y ?? '', pe.vx ?? '', pe.vy ?? '', pe.Ek ?? '', pe.Ep ?? '', pe.Em ?? '',
        pr.time ?? '', pr.x ?? '', pr.y ?? '', pr.vx ?? '', pr.vy ?? '', pr.Ek ?? '', pr.Ep ?? '', pr.Em ?? '',
      ];
      rows.push(row.join(','));
    }

    const blob = new Blob([rows.join('\r\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `projectile_trajectory_${Date.now()}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  // ==========================================
  // 9. EVENT LISTENERS & INITIALIZATION
  // ==========================================
  buttons.launch.addEventListener('click', () => fetchSimulationData());
  buttons.exportCsv.addEventListener('click', () => exportCSV());
  buttons.replay.addEventListener('click', () => {
    if (simulationData) startAnimation();
  });

  buttons.reset.addEventListener('click', () => {
    inputs.v0_num.value = 50;
    inputs.v0_range.value = 50;
    inputs.angle_num.value = 45;
    inputs.angle_range.value = 45;
    inputs.mass_num.value = 1.0;
    inputs.mass_range.value = 1.0;
    inputs.k_num.value = 0.010;
    inputs.k_range.value = 0.010;
    inputs.wind_num.value = 0;
    inputs.wind_range.value = 0;

    toggles.ideal.checked = true;
    toggles.euler.checked = true;
    toggles.rk4.checked = true;

    updateWindBadge();
    fetchSimulationData();
  });

  [toggles.ideal, toggles.euler, toggles.rk4].forEach((tg) => {
    tg.addEventListener('change', () => {
      updateMetrics();
      renderCanvas(animProgress);
    });
  });

  chartViewMode.addEventListener('change', () => renderEnergyChart(animProgress));
  window.addEventListener('resize', resizeCanvas);

  // Canvas Hover Coordinate Tooltip
  canvas.addEventListener('mousemove', (e) => {
    if (!simulationData) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    if (
      mouseX < transform.padLeft ||
      mouseX > transform.padLeft + transform.plotWidth ||
      mouseY < transform.padTop ||
      mouseY > transform.padTop + transform.plotHeight
    ) {
      canvasTooltip.classList.add('hidden');
      return;
    }

    const [physX, physY] = toPhysicsCoords(mouseX, mouseY);
    if (physY < 0) {
      canvasTooltip.classList.add('hidden');
      return;
    }

    canvasTooltip.classList.remove('hidden');
    canvasTooltip.style.left = `${mouseX + 14}px`;
    canvasTooltip.style.top = `${mouseY - 14}px`;
    canvasTooltip.innerHTML = `x: <strong class="text-white">${physX.toFixed(1)}m</strong>, y: <strong class="text-cyan-400">${physY.toFixed(1)}m</strong>`;
  });

  canvas.addEventListener('mouseleave', () => {
    canvasTooltip.classList.add('hidden');
  });

  // Initial Boot
  initEnergyChart();
  updateWindBadge();
  resizeCanvas();
  fetchSimulationData();
})();
