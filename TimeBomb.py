from flask import Flask, render_template_string, request, redirect, url_for
import time

app = Flask(__name__)

# === Circuit state ===
circuit = {
	"entry_diodes": {"locked": False, "last_signal": None},
	"bidirectional": {"a": None, "b": None},
	"oscillator_tick": False,
	"tick_count": 0
}

# Toggle oscillator (simulate ticking)
def tick_oscillator():
	circuit["oscillator_tick"] = not circuit["oscillator_tick"]
	circuit["tick_count"] += 1
	# Bidirectional diodes update
	signal = "tick" if circuit["oscillator_tick"] else None
	circuit["bidirectional"]["a"] = signal
	circuit["bidirectional"]["b"] = signal

# HTML template (no JS, pure server-rendered)
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
</style>
</head>
<body>
<h1>Python Diode Circuit (Server-Side)</h1>

<div class="oscillator">
  <h2>Oscillator</h2>
  <p>Tick: <span class="signal">{{ 'ON' if oscillator else 'OFF' }}</span></p>
  <p>Tick count: {{ tick_count }}</p>
  <form method="post" action="{{ url_for('tick') }}">
	<button type="submit">Toggle Oscillator</button>
  </form>
</div>

<div class="diode">
  <h2>Entry Diode</h2>
  <p>Status: <span class="signal">{{ 'Passed' if entry_pass else 'Blocked' }}</span></p>
  <form method="post" action="{{ url_for('entry') }}">
	<button type="submit">Send Entry Signal</button>
  </form>
  <form method="post" action="{{ url_for('reset_entry') }}">
	<button type="submit">Reset Entry Diode</button>
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

# === Routes ===

@app.route("/")
def index():
	return render_template_string(
		HTML_TEMPLATE,
		oscillator=circuit["oscillator_tick"],
		tick_count=circuit["tick_count"],
		entry_pass=circuit["entry_diodes"]["last_signal"] == "entry_signal",
		bidirectional=circuit["bidirectional"]
	)

@app.route("/tick", methods=["POST"])
def tick():
	tick_oscillator()
	return redirect(url_for('index'))

@app.route("/entry", methods=["POST"])
def entry():
	if not circuit["entry_diodes"]["locked"]:
		circuit["entry_diodes"]["locked"] = True
		circuit["entry_diodes"]["last_signal"] = "entry_signal"
	return redirect(url_for('index'))

@app.route("/reset_entry", methods=["POST"])
def reset_entry():
	circuit["entry_diodes"]["locked"] = False
	circuit["entry_diodes"]["last_signal"] = None
	return redirect(url_for('index'))

if __name__ == "__main__":
	app.run(debug=True)