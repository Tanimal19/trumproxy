from flask import Flask, request, jsonify, render_template
from trumproxy import proxy_instance, TariffRule
from flask_cors import CORS
import json
import os

RULES_FILE = "rules.json"

app = Flask(__name__)
CORS(app)


# Load rules from the JSON file
if not os.path.exists(RULES_FILE):
    with open(RULES_FILE, "w") as f:
        json.dump({}, f, indent=2)

with open(RULES_FILE, "r") as f:
    data = json.load(f)

for country_code, rule_data in data.items():
    proxy_instance.set_tariff_rule(
        country_code, tariff=rule_data["rate"], dropped=rule_data["dropped"]
    )


def save_rules():
    data = {
        country: {"rate": rule.rate, "dropped": rule.dropped}
        for country, rule in proxy_instance.get_tariff_rules().items()
    }
    with open(RULES_FILE, "w") as f:
        json.dump(data, f, indent=2)


# Endpoints
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/api/rules/<country_code>", methods=["POST"])
def add_rule(country_code):
    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    rule_map = proxy_instance.get_tariff_rules()
    if country_code in rule_map:
        return jsonify({"error": "Rule already exist"}), 404

    delay_percentage = data.get("delay_percentage", 0)
    drop = data.get("drop", False)

    proxy_instance.set_tariff_rule(country_code, delay_percentage, drop)
    save_rules()

    return jsonify({"message": "Rule added successfully"}), 200


@app.route("/api/rules/<country_code>", methods=["PUT"])
def update_rule(country_code):
    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    delay_percentage = data.get("delay_percentage", 0)
    drop = data.get("drop", False)

    proxy_instance.set_tariff_rule(country_code, delay_percentage, drop)
    save_rules()

    return jsonify({"message": "Rule updated successfully"}), 200


@app.route("/api/rules/<country_code>", methods=["DELETE"])
def delete_rule(country_code):
    proxy_instance.remove_tariff_rule(country_code)
    save_rules()

    return jsonify({"message": "Rule deleted successfully"}), 200


@app.route("/api/rules", methods=["GET"])
def get_rules():
    rules = [
        {
            "country_code": country_code,
            "delay_percentage": rule.rate,
            "drop": rule.dropped,
        }
        for country_code, rule in proxy_instance.get_tariff_rules().items()
    ]
    return jsonify({"rules": rules})


@app.route("/api/packets", methods=["GET"])
def get_packets():

    packets = [
        {
            "packet_id": flow_id,
            "url": packet.request_url,
            "size": packet.size,
            "source_ip": packet.from_ip,
            "source_country": packet.from_country_code,
            "recv_time": packet.recv_time,
            "rtt_time": packet.rtt_time,
            "retain_time": packet.retain_time,
            "status": packet.status,
        }
        for flow_id, packet in proxy_instance.get_cached_packets().items()
    ]
    proxy_instance.clean_cached_packets()

    return jsonify({"packets": packets}), 200
