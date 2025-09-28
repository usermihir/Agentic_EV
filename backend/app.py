from flask import Flask, jsonify, request

app = Flask(__name__)

# Dummy charger data
stations = {
    "Station_A": {"ports": 2, "occupied": 1, "health": 0.9},
    "Station_B": {"ports": 3, "occupied": 2, "health": 0.7},
    "Station_C": {"ports": 1, "occupied": 0, "health": 1.0},
}

# Simple EV station assignment
@app.route("/assign_station", methods=["POST"])
def assign_station():
    ev = request.json
    soc = ev.get("soc", 50)  # default SOC if not provided

    # Pick station with most free ports
    best_station = None
    best_score = -1
    for name, data in stations.items():
        free_ports = data["ports"] - data["occupied"]
        score = free_ports * data["health"] * (100 - soc)  # prioritize low SOC
        if score > best_score:
            best_score = score
            best_station = name

    if best_station:
        stations[best_station]["occupied"] += 1
        return jsonify({"assigned_station": best_station})
    else:
        return jsonify({"error": "No available stations"}), 400

# Charger health API
@app.route("/charger_health", methods=["GET"])
def charger_health():
    health_info = [{"name": name, "health": data["health"]} for name, data in stations.items()]
    return jsonify(health_info)

if __name__ == "__main__":
    app.run(debug=True)
