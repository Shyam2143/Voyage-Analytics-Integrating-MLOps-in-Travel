
"""
Flight Price Predictor - Flask REST API + HTML UI
"""

import os, json, logging
import joblib
import pandas as pd
from flask import Flask, render_template_string, request, jsonify

# ── Logging ──────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# 1. CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
MODEL_PATH   = os.path.join(os.path.dirname(__file__), "best_flight_price_model.joblib")
HOST         = "0.0.0.0"
PORT         = 8000

# ═══════════════════════════════════════════════════════════════════════════
# 2. LOAD THE TRAINED MODEL
# ════════════════════
model = None
try:
    model = joblib.load(MODEL_PATH)
    log.info("Model loaded from %s", MODEL_PATH)
except Exception as exc:
    log.error("Could not load model: %s", exc)

# ── Exact column schema the model was trained on (EXCLUDES 'price') ──────
FEATURE_COLUMNS = [
    "time", "distance", "month", "day", "day_of_week", "is_weekend",
    "from_Aracaju (SE)", "from_Brasilia (DF)", "from_Campo Grande (MS)",
    "from_Florianopolis (SC)", "from_Natal (RN)", "from_Recife (PE)",
    "from_Rio de Janeiro (RJ)", "from_Salvador (BH)", "from_Sao Paulo (SP)",
    "destination_Aracaju (SE)", "destination_Brasilia (DF)",
    "destination_Campo Grande (MS)", "destination_Florianopolis (SC)",
    "destination_Natal (RN)", "destination_Recife (PE)",
    "destination_Rio de Janeiro (RJ)", "destination_Salvador (BH)",
    "destination_Sao Paulo (SP)", "flightType_economic",
    "flightType_firstClass", "flightType_premium", "agency_CloudFy",
    "agency_FlyingDrops", "agency_Rainbow",
]

CITIES = [
    "Aracaju (SE)", "Brasilia (DF)", "Campo Grande (MS)",
    "Florianopolis (SC)", "Natal (RN)", "Recife (PE)",
    "Rio de Janeiro (RJ)", "Salvador (BH)", "Sao Paulo (SP)",
]

# ═══════════════════════════════════════════════════════════════════════════
# 3. EMBEDDED HTML UI  (responsive, accessible)
# ═══════════════════════════════════════════════════════════════════════════
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flight Price Predictor</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .card {
            background: #ffffff;
            border-radius: 20px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.35);
            width: 100%;
            max-width: 820px;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 28px 32px;
            text-align: center;
        }
        .header h1 { font-size: 26px; font-weight: 700; letter-spacing: -0.5px; }
        .header .badge-row {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-top: 10px;
            flex-wrap: wrap;
        }
        .badge {
            font-size: 12px;
            padding: 5px 14px;
            border-radius: 20px;
            font-weight: 600;
        }
        .badge.ok    { background: #28a745; }
        .badge.fail  { background: #dc3545; }
        .badge.info  { background: rgba(255,255,255,0.25); }

        .body { padding: 30px 32px; }
        .form-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }
        @media (max-width: 600px) { .form-grid { grid-template-columns: 1fr; } }

        label { font-weight: 600; font-size: 13px; color: #444; display: block; margin-bottom: 4px; }
        input, select {
            width: 100%;
            padding: 10px 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: 0.2s;
            background: #fafafa;
        }
        input:focus, select:focus { border-color: #667eea; outline: none; background: #fff; }

        .btn {
            width: 100%;
            padding: 14px;
            margin-top: 22px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: opacity 0.2s, transform 0.1s;
        }
        .btn:hover { opacity: 0.92; }
        .btn:active { transform: scale(0.98); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }

        .result-box {
            margin-top: 20px;
            padding: 18px 20px;
            border-radius: 10px;
            text-align: center;
            font-weight: 700;
            font-size: 17px;
            display: none;
        }
        .result-box.show { display: block; }
        .result-box.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .result-box.error   { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }

    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1>Flight Price Predictor</h1>
            <div class="badge-row">
                <span class="badge {{ 'ok' if model_loaded else 'fail' }}">
                    Model: {{ 'Loaded' if model_loaded else 'Not Found' }}
                </span>
            </div>
        </div>
        <div class="body">

            <form id="predictForm">
                <div class="form-grid">
                    <div>
                        <label>Time</label>
                        <input type="number" name="time" step="0.01" required placeholder="e.g. 14.50">
                    </div>
                    <div>
                        <label>Distance</label>
                        <input type="number" name="distance" step="0.01" required placeholder="e.g. 850.0">
                    </div>
                    <div>
                        <label>Month</label>
                        <input type="number" name="month" min="1" max="12" required placeholder="1–12">
                    </div>
                    <div>
                        <label>Day (day-of-year ID)</label>
                        <input type="number" name="day" required placeholder="e.g. 180">
                    </div>
                    <div>
                        <label>Day of Week (0=Mon … 6=Sun)</label>
                        <input type="number" name="day_of_week" min="0" max="6" required placeholder="0–6">
                    </div>
                    <div>
                        <label>Is Weekend?</label>
                        <select name="is_weekend" required>
                            <option value="0">No</option>
                            <option value="1">Yes</option>
                        </select>
                    </div>
                    <div>
                        <label>Origin City</label>
                        <select name="from_city" required>
                            <option value="">Choose …</option>
                            {% for c in cities %}
                            <option value="{{ c }}">{{ c }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div>
                        <label>Destination City</label>
                        <select name="destination" required>
                            <option value="">Choose …</option>
                            {% for c in cities %}
                            <option value="{{ c }}">{{ c }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div>
                        <label>Flight Type</label>
                        <select name="flightType" required>
                            <option value="">Choose …</option>
                            <option value="economic">Economic</option>
                            <option value="firstClass">First Class</option>
                            <option value="premium">Premium</option>
                        </select>
                    </div>
                    <div>
                        <label>Agency</label>
                        <select name="agency" required>
                            <option value="">Choose …</option>
                            <option value="CloudFy">CloudFy</option>
                            <option value="FlyingDrops">FlyingDrops</option>
                            <option value="Rainbow">Rainbow</option>
                        </select>
                    </div>
                </div>
                <button type="submit" class="btn" id="submitBtn">Predict Price</button>
            </form>

            <div id="resultBox" class="result-box"></div>
        </div>
    </div>

    <script>
        const form = document.getElementById('predictForm');
        const btn   = document.getElementById('submitBtn');
        const box   = document.getElementById('resultBox');

        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            box.className = 'result-box';
            btn.disabled = true;
            btn.textContent = 'Predicting …';

            const fd = new FormData(form);
            const payload = {};
            for (const [k, v] of fd.entries()) {
                if (['month','day','day_of_week','is_weekend'].includes(k))
                    payload[k] = parseInt(v, 10);
                else if (['time','distance'].includes(k))
                    payload[k] = parseFloat(v);
                else
                    payload[k] = v;
            }

            try {
                const resp = await fetch('/predict', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                const data = await resp.json();
                if (resp.ok) {
                    box.className = 'result-box show success';
                    box.innerHTML = '<strong>Predicted Price:</strong> ' + data.predicted_price;
                } else {
                    box.className = 'result-box show error';
                    box.innerHTML = (data.error || 'Prediction failed');
                }
            } catch (err) {
                box.className = 'result-box show error';
                box.innerHTML = 'Network Error: ' + err.message;
            } finally {
                btn.disabled = false;
                btn.textContent = 'Predict Price';
            }
        });
    </script>
</body>
</html>"""

# ═══════════════════════════════════════════════════════════════════════════
# 4. FLASK APP
# ═══════════════════════════════════════════════════════════════════════════
app = Flask(__name__)

@app.route("/")
def home():
    return render_template_string(
        HTML_TEMPLATE,
        model_loaded=model is not None,
        cities=CITIES,
    )


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None,
        "model_path": MODEL_PATH,
        "features": len(FEATURE_COLUMNS),
    })


@app.route("/predict", methods=["POST"])
def predict():
    if model is None:
        return jsonify({"error": "Model not loaded"}), 503

    try:
        data = request.get_json(force=True)

        # Build one-hot row
        row = {col: 0 for col in FEATURE_COLUMNS}

        # Numeric / boolean
        row["time"]        = float(data.get("time", 0))
        row["distance"]    = float(data.get("distance", 0))
        row["month"]       = int(data.get("month", 0))
        row["day"]         = int(data.get("day", 0))
        row["day_of_week"] = int(data.get("day_of_week", 0))
        row["is_weekend"]  = int(data.get("is_weekend", 0))

        # Origin city
        fc = data.get("from_city")
        if fc:
            col = f"from_{fc}"
            if col in row:
                row[col] = 1

        # Destination city
        dc = data.get("destination")
        if dc:
            col = f"destination_{dc}"
            if col in row:
                row[col] = 1

        # Flight type
        ft = data.get("flightType")
        if ft:
            col = f"flightType_{ft}"
            if col in row:
                row[col] = 1

        # Agency
        ag = data.get("agency")
        if ag:
            col = f"agency_{ag}"
            if col in row:
                row[col] = 1

        df = pd.DataFrame([row])[FEATURE_COLUMNS]
        pred = float(model.predict(df)[0])

        log.info("Prediction: %.2f | from=%s → to=%s | class=%s | agency=%s",
                 pred, fc, dc, ft, ag)

        return jsonify({"predicted_price": round(pred, 2)})

    except Exception as exc:
        log.exception("Prediction error")
        return jsonify({"error": str(exc)}), 400


# ═══════════════════════════════════════════════════════════════════════════
# 5. MAIN — run the app
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("FLIGHT PRICE PREDICTOR")
    print("=" * 60)
    print(f"Local URL  : http://{HOST}:{PORT}")
    print(f"Model      : {MODEL_PATH}  {'loaded' if model else 'MISSING'}")
    print("=" * 60)
    app.run(host=HOST, port=PORT, debug=False)