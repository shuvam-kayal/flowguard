# Income Forecasting — Person 2

This folder forecasts the next 7 and 30 days of income and converts the risk
into Financial Weather. It always returns the shared `ForecastResult` contract
used by the backend, resilience engine, and frontend.

## 1. One-time setup (Windows PowerShell)

Run these commands from the repository root (`C:\Projects\flowguard`):

```powershell
python -m pip install -r requirements.txt pytest
```

`pytest` is installed explicitly because it is a development test dependency,
not an application dependency in `requirements.txt`.

## 2. Run the complete automated forecast check

```powershell
python -m pytest -q forecast/test_forecast_pipeline.py
python -m pytest -q tests/test_flowguard.py -k forecast
```

The first command is the complete Person 2 test. It creates temporary dated
income, trains a model, evaluates it out-of-time, loads that model, and checks
the final API object. It does not write a model or CSV into the repository.

The second command checks compatibility with the shared FlowGuard integration.

Both commands must finish with `passed`.

## 3. What a passing run guarantees

- A trained model can be created and evaluated.
- The fallback still works if there is little/no income history or no model.
- `daily_forecast` has exactly 30 points.
- `next_7_days` and `next_30_days` equal the sums of the returned daily points.
- Every point has `lower <= expected <= upper`.
- `shock_probability` is between `0` and `1`.
- `weather` is `STABLE`, `WATCH`, or `SHOCK`.
- The object validates as the team's `ForecastResult` contract.

## 4. Train with real historical income (optional)

Create a CSV outside source control (for example `my_income_history.csv`) with
at least 40 daily rows for a worker; 60+ is preferable:

```csv
worker_id,date,income
W001,2026-01-01,650
W001,2026-01-02,820
W001,2026-01-03,0
```

`date` must be ISO format (`YYYY-MM-DD`). `amount` can be used instead of
`income`. Extra fields such as `platform` and `hours_worked` are safe to keep,
but the current model does not use them yet.

Train and save the artifact used automatically by `predict.py`:

```powershell
python forecast/train.py C:\path\to\my_income_history.csv
```

Expected output includes `training_examples`, `validation_examples`, and `mae`.
This writes `forecast/income_model.joblib`; do not commit that generated file.

Evaluate on each worker's final 20% of dates (never a random split):

```powershell
python forecast/evaluate.py C:\path\to\my_income_history.csv
```

Expected output:

```text
{'observations': ..., 'mae': ..., 'rmse': ...}
```

`mae` is the average daily error in rupees and is the main accuracy metric to
report. Lower is better.

## 5. End-to-end API smoke test

Start the backend in one PowerShell window:

```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

In a second window, run this request. It uses the team's W001 profile and a
30-day earnings history, so it verifies the endpoint that teammates call:

```powershell
$profile = (Get-Content data\demo\personas.json -Raw | ConvertFrom-Json).personas |
    Where-Object worker_id -eq 'W001'
$history = 1..30 | ForEach-Object {
    @{ date = (Get-Date).Date.AddDays(-$_).ToString('yyyy-MM-dd'); amount = (650 + ($_ % 7) * 60); type = 'CREDIT' }
}
$body = @{ profile = $profile; history = $history } | ConvertTo-Json -Depth 6
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/forecast/income `
    -ContentType 'application/json' -Body $body | ConvertTo-Json -Depth 6
```

Confirm the response contains:

```text
worker_id, next_7_days, next_30_days, lower_bound, upper_bound,
trend, shock_probability, weather, daily_forecast
```

and that `daily_forecast` contains 30 dated points. That is the full output
contract required by the other modules.

## How prediction chooses its method

- With `forecast/income_model.joblib` and 28+ daily history points: use the
  trained Random Forest model.
- Otherwise: use the transparent rolling-average, trend, volatility, and
  weekday fallback.

This means the API remains available for new workers while a trained model is
used for workers with sufficient history.
