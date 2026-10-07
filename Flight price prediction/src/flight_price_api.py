
"""
Flight Price Predictor - Flask REST API + HTML UI
"""

import logging
import os
from datetime import date
from pathlib import Path
import joblib
import pandas as pd
from flask import Flask, render_template_string, request, jsonify

# Print useful messages in the terminal while the app is running.
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# --- App settings ---------------------------------------------------------
PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
MODEL_PATH = os.environ.get(
    "FLIGHT_PRICE_MODEL_PATH",
    str(PROJECT_DIRECTORY / "artifacts" / "best_flight_price_model.joblib"),
)
HOST = "0.0.0.0"
PORT = 8000

# Load the machine-learning model once, when this file starts.
flight_price_model = None
try:
    flight_price_model = joblib.load(MODEL_PATH)
    log.info("Model loaded from %s", MODEL_PATH)
except Exception as exc:
    log.error("Could not load model: %s", exc)

# The model was trained with these 30 columns, in exactly this order.
# Do not remove or reorder them unless the model is trained again.
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

# During training, pandas turned each text value into columns such as
# "agency_Rainbow" and "flightType_economic". This dictionary tells the app
# how a form field maps to those columns.
FORM_FIELD_PREFIXES = {
    "from_city": "from_",
    "destination": "destination_",
    "flightType": "flightType_",
    "agency": "agency_",
}


def get_dropdown_options(field_name):
    """Find valid dropdown values from the model's feature-column names."""
    prefix = FORM_FIELD_PREFIXES[field_name]
    return [column.removeprefix(prefix) for column in FEATURE_COLUMNS if column.startswith(prefix)]


FORM_OPTIONS = {
    field_name: get_dropdown_options(field_name)
    for field_name in FORM_FIELD_PREFIXES
}


def create_model_input(form_data):
    """Convert simple form values into the numeric row required by the model."""
    try:
        selected_date = date.fromisoformat(str(form_data["travel_date"]))
        values = {
            "time": float(form_data["time"]),
            "distance": float(form_data["distance"]),
            "month": selected_date.month,
            "day": selected_date.day,
            "day_of_week": selected_date.weekday(),
            "is_weekend": int(selected_date.weekday() >= 5),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Enter a valid date, time, and distance.") from exc

    # One-hot encoding in plain language:
    #   1. Every category column starts as 0.
    #   2. The column for the user's selected option becomes 1.
    for field_name, prefix in FORM_FIELD_PREFIXES.items():
        selected_value = form_data.get(field_name)
        selected_column = f"{prefix}{selected_value}"
        if selected_column not in FEATURE_COLUMNS:
            friendly_name = field_name.replace("_", " ")
            raise ValueError(f"Choose a valid {friendly_name}.")
        values[selected_column] = 1

    # Missing columns become 0. columns=FEATURE_COLUMNS also keeps the order
    # identical to the data used when the model was trained.
    return pd.DataFrame([values], columns=FEATURE_COLUMNS).fillna(0)

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
                        <label>Travel Date</label>
                        <input type="date" name="travel_date" required>
                    </div>
                    <div>
                        <label>Origin City</label>
                        <select name="from_city" required>
                            <option value="">Choose …</option>
                            {% for c in choices.from_city %}
                            <option value="{{ c }}">{{ c }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div>
                        <label>Destination City</label>
                        <select name="destination" required>
                            <option value="">Choose …</option>
                            {% for c in choices.destination %}
                            <option value="{{ c }}">{{ c }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div>
                        <label>Flight Type</label>
                        <select name="flightType" required>
                            <option value="">Choose …</option>
                            {% for option in choices.flightType %}
                            <option value="{{ option }}">{{ option }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div>
                        <label>Agency</label>
                        <select name="agency" required>
                            <option value="">Choose …</option>
                            {% for option in choices.agency %}
                            <option value="{{ option }}">{{ option }}</option>
                            {% endfor %}
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
                if (['time','distance'].includes(k))
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
        model_loaded=flight_price_model is not None,
        choices=FORM_OPTIONS,
    )


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "model_loaded": flight_price_model is not None,
        "model_path": MODEL_PATH,
        "features": len(FEATURE_COLUMNS),
    })


@app.route("/predict", methods=["POST"])
def predict():
    if flight_price_model is None:
        return jsonify({"error": "Model not loaded"}), 503

    try:
        form_data = request.get_json(silent=True)
        if not isinstance(form_data, dict):
            return jsonify({"error": "Send a JSON object."}), 400

        model_input = create_model_input(form_data)
        # The saved model was trained with an array, so send the values only.
        # create_model_input has already put them in the correct column order.
        predicted_price = float(flight_price_model.predict(model_input.to_numpy())[0])

        origin = form_data["from_city"]
        destination = form_data["destination"]
        flight_type = form_data["flightType"]
        agency = form_data["agency"]

        log.info("Prediction: %.2f | from=%s → to=%s | class=%s | agency=%s",
                 predicted_price, origin, destination, flight_type, agency)

        return jsonify({"predicted_price": round(predicted_price, 2)})

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
    print(f"Model      : {MODEL_PATH}  {'loaded' if flight_price_model else 'MISSING'}")
    print("=" * 60)
    app.run(host=HOST, port=PORT, debug=False)
