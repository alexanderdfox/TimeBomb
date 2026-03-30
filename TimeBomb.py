from flask import Flask, render_template_string, request, redirect, url_for
import time

app = Flask(__name__)

# === Circuit state ===
circuit = {
    "entry_diodes": {"last_click": 0, "last_signal": None},
    "bidirectional": {"a": None, "b": None},
    "oscillator_tick": False,
    "tick_count": 0,
    "last_osc_tick": time.time()
}

# Oscillator: always-on, toggles tick every second
def tick_oscillator():
    now = time.time()
    if now - circuit["last_osc_tick"] >= 1:  # 1-second tick
        circuit["oscillator_tick"] = not circuit["oscillator_tick"]
        circuit["tick_count"] += 1
        circuit["bidirectional"]["a"] = "tick" if circuit["oscillator_tick"] else None
        circuit["bidirectional"]["b"] = "tick" if circuit["oscillator_tick"] else None
        circuit["last_osc_tick"] = now

# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Python Diode Circuit</title>
<style>
  body { font-family: monospace; background: #111; color: #0f0; padding: 2rem; }
  .diode, .bidirectional, .oscillator { border: 1px solid #0f0; padding: 1rem; margin: 1rem; width: 300px; text-align: center; }
  .signal { font-weight: bold; }
  button { background: #111; color: #0f0; border: 1px solid #0f0; padding: 0.5rem 1rem; cursor: pointer; margin: 0.5rem; }
  button:disabled { color: #333; border-color: #333; cursor: not-allowed; }
</style>
<meta http-equiv="refresh" content="1">
</head>
<body>
<h1>Python Diode Circuit (Server-Side)</h1>

<div class="oscillator">
  <h2>Oscillator</h2>
  <p>Tick: <span class="signal">{{ 'ON' if oscillator else 'OFF' }}</span></p>
  <p>Tick count: {{ tick_count }}</p>
</div>

<div class="diode">
  <h2>Entry Diode</h2>
  <p>Status: <span class="signal">{{ entry_status }}</span></p>
  <form method="post" action="{{ url_for('entry') }}">
    <button type="submit" {{ 'disabled' if not can_click else '' }}>Send Entry Signal</button>
  </form>
</div>

<div class="bidirectional">
  <h2>Bidirectional Diodes</h2>
  <p>A-side: <span class="signal">{{ bidirectional.a or '-' }}</span></p>
  <p>B-side: <span class="signal">{{ bidirectional.b or '-' }}</span></p>
</div>

</body>
</html>
"""

@app.route("/")
def index():
    tick_oscillator()
    # Entry diode click allowed only every 10 seconds
    now = time.time()
    can_click = (now - circuit["entry_diodes"]["last_click"]) >= 10
    entry_status = "Passed" if circuit["entry_diodes"]["last_signal"] == "entry_signal" else "Blocked"
    return render_template_string(
        HTML_TEMPLATE,
        oscillator=circuit["oscillator_tick"],
        tick_count=circuit["tick_count"],
        bidirectional=circuit["bidirectional"],
        entry_status=entry_status,
        can_click=can_click
    )

@app.route("/entry", methods=["POST"])
def entry():
    now = time.time()
    if (now - circuit["entry_diodes"]["last_click"]) >= 10:
        circuit["entry_diodes"]["last_click"] = now
        circuit["entry_diodes"]["last_signal"] = "entry_signal"
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
