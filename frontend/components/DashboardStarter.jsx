// FlowGuard — Dashboard STARTER for Person 5.
// This is a functional wiring reference, NOT the final design.
// It proves the data flow end-to-end so you can immediately start designing
// the 5 hero screens. Replace styling with your own design language.
//
// Screens to build (see docs/api-contract.md for exact data):
//   1. Dashboard      -> resilience.safe_to_spend_daily (HERO), score, days, weather
//   2. Financial Weather -> forecast.daily_forecast (chart) + weather status
//   3. Resilience Wallet -> resilience.wallet_allocation (4 buckets)
//   4. Intervention   -> recommendations[] + the SIMULATE SHOCK button
//   5. Credit Guard   -> POST /credit/evaluate waterfall
//
// The SIMULATE SHOCK / RECOVERY buttons are your killer live demo moment.

import { useEffect, useState } from "react";
import { api } from "../lib/api";

const WEATHER_ICON = { STABLE: "☀️", WATCH: "🌤️", SHOCK: "🌧️" };
const MODE_COLOR = {
  NORMAL: "#16a34a", RECOVERY: "#16a34a",
  WATCH: "#d97706", SHOCK: "#dc2626",
};

export default function DashboardStarter() {
  const [workers, setWorkers] = useState([]);
  const [workerId, setWorkerId] = useState("W001");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function load(id) {
    setLoading(true);
    setError(null);
    try {
      setData(await api.dashboard(id));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    api.listWorkers().then(setWorkers).catch(() => {});
    load(workerId);
  }, []);

  async function onShock() {
    setData(await api.simulateShock(workerId));
  }
  async function onRecovery() {
    setData(await api.simulateRecovery(workerId));
  }
  function onSelect(id) {
    setWorkerId(id);
    load(id);
  }

  if (loading) return <div style={{ padding: 24 }}>Loading…</div>;
  if (error)
    return (
      <div style={{ padding: 24 }}>
        Couldn’t reach the backend ({error}). Start it with{" "}
        <code>uvicorn backend.main:app --reload</code>, or load the bundled mock.
      </div>
    );
  if (!data) return null;

  const { worker, risk, forecast, resilience, recommendations } = data;

  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: 24, fontFamily: "system-ui" }}>
      {/* worker switcher */}
      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        {workers.map((w) => (
          <button
            key={w.worker_id}
            onClick={() => onSelect(w.worker_id)}
            style={{
              padding: "6px 12px", borderRadius: 8,
              border: w.worker_id === workerId ? "2px solid #111" : "1px solid #ccc",
              background: w.worker_id === workerId ? "#111" : "#fff",
              color: w.worker_id === workerId ? "#fff" : "#111", cursor: "pointer",
            }}
          >
            {w.name.split(" ")[0]}
          </button>
        ))}
      </div>

      <h2 style={{ margin: "0 0 4px" }}>{worker.name}</h2>
      <p style={{ margin: "0 0 24px", color: "#666" }}>{worker.occupation}</p>

      {/* HERO: safe-to-spend */}
      <div style={{ textAlign: "center", padding: "32px 0", borderRadius: 16, background: "#f7f7f5" }}>
        <div style={{ fontSize: 64, fontWeight: 700, lineHeight: 1 }}>
          ₹{resilience.safe_to_spend_daily}
        </div>
        <div style={{ color: "#666", marginTop: 8, letterSpacing: 0.5 }}>Safe to spend today</div>
      </div>

      {/* stat row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginTop: 16 }}>
        <Stat label="Resilience" value={`${resilience.resilience_score}/100`} />
        <Stat label="Cover" value={`${resilience.resilience_days} days`} />
        <Stat
          label="Weather"
          value={`${WEATHER_ICON[forecast.weather]} ${forecast.weather}`}
        />
      </div>

      <div style={{ marginTop: 8, color: MODE_COLOR[resilience.mode], fontWeight: 600 }}>
        Mode: {resilience.mode} · Risk: {risk.risk_level}
      </div>

      {/* recommendations */}
      <h3 style={{ marginTop: 24 }}>What FlowGuard suggests</h3>
      {recommendations.map((r, i) => (
        <div key={i} style={{ padding: 12, border: "1px solid #eee", borderRadius: 10, marginBottom: 8 }}>
          <strong>{r.message}</strong>
          <div style={{ color: "#888", fontSize: 13 }}>{r.reason}</div>
        </div>
      ))}

      {/* the live demo buttons */}
      <div style={{ display: "flex", gap: 12, marginTop: 24 }}>
        <button onClick={onShock} style={btn("#dc2626")}>Simulate income shock</button>
        <button onClick={onRecovery} style={btn("#16a34a")}>Simulate recovery</button>
        <button onClick={() => load(workerId)} style={btn("#555")}>Reset</button>
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div style={{ padding: 12, border: "1px solid #eee", borderRadius: 10, textAlign: "center" }}>
      <div style={{ fontSize: 18, fontWeight: 700 }}>{value}</div>
      <div style={{ fontSize: 12, color: "#888" }}>{label}</div>
    </div>
  );
}

const btn = (bg) => ({
  padding: "10px 16px", borderRadius: 8, border: "none",
  background: bg, color: "#fff", cursor: "pointer", fontWeight: 600,
});
