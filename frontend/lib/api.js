// FlowGuard API client — Person 5 imports from here.
// Points at Person 4's FastAPI. Swap BASE_URL if backend runs elsewhere.
// Every function returns data in the exact shapes from docs/api-contract.md.

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function j(path, opts = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) throw new Error(`API ${path} -> ${res.status}`);
  return res.json();
}

export const api = {
  listWorkers: () => j("/workers"),
  dashboard: (workerId) => j(`/worker/${workerId}/dashboard`),
  evaluateCredit: (workerId, requestedAmount) =>
    j("/credit/evaluate", {
      method: "POST",
      body: JSON.stringify({ worker_id: workerId, requested_amount: requestedAmount }),
    }),
  simulateShock: (workerId, factor = 0.65) =>
    j("/simulate/shock", {
      method: "POST",
      body: JSON.stringify({ worker_id: workerId, factor }),
    }),
  simulateRecovery: (workerId) =>
    j("/simulate/recovery", {
      method: "POST",
      body: JSON.stringify({ worker_id: workerId }),
    }),
};

// Day-1 fallback: if backend isn't up yet, Person 5 can import these mocks directly.
// Copy data/demo/sample_dashboards.json into frontend/public/ and fetch it, OR
// import a bundled copy. This keeps frontend unblocked with zero backend dependency.
