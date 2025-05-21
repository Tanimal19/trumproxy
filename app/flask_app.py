from flask import Flask, request, jsonify, render_template
from trumproxy import proxy_instance
from flask_cors import CORS
import json
import os

RULES_FILE = "rules.json"

app = Flask(__name__)
CORS(app)

rule_id_counter = 1
rule_id_map = {}  # rule_id -> country_code
country_code_map = {}  # country_code -> rule_id


def sync_rule_ids():
    global rule_id_counter
    for country_code in proxy_instance.get_tariff_rules():
        if country_code not in country_code_map:
            rule_id = rule_id_counter
            rule_id_map[rule_id] = country_code
            country_code_map[country_code] = rule_id
            rule_id_counter += 1


def save_rules():
    sync_rule_ids()
    data = {
        "rule_id_map": {str(k): v for k, v in rule_id_map.items()},
        "rules": {
            country: {"rate": rule.rate, "dropped": rule.dropped}
            for country, rule in proxy_instance.get_tariff_rules().items()
        },
    }
    with open(RULES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_rules():
    global rule_id_counter, rule_id_map, country_code_map

    if not os.path.exists(RULES_FILE):
        return

    with open(RULES_FILE, "r") as f:
        data = json.load(f)

    rule_id_map = {int(k): v for k, v in data.get("rule_id_map", {}).items()}
    country_code_map = {v: k for k, v in rule_id_map.items()}
    rule_id_counter = max(rule_id_map.keys(), default=0) + 1

    for country_code, rule_data in data.get("rules", {}).items():
        proxy_instance.set_tariff_rule(
            country_code, tariff=rule_data["rate"], dropped=rule_data["dropped"]
        )


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/api/rules", methods=["POST"])
def add_rule():
    global rule_id_counter
    data = request.json

    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    country_code = data.get("country_code")
    delay_percentage = data.get("delay_percentage", 0)
    drop = data.get("drop", False)

    if not country_code:
        return jsonify({"error": "Missing country_code"}), 400

    proxy_instance.set_tariff_rule(country_code, delay_percentage, drop)
    rule_id = rule_id_counter
    rule_id_map[rule_id] = country_code
    country_code_map[country_code] = rule_id
    rule_id_counter += 1
    save_rules()
    return jsonify({"message": "Rule added successfully", "rule_id": rule_id})


@app.route("/api/rules/<int:rule_id>", methods=["PUT"])
def update_rule(rule_id):
    data = request.json

    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    delay_percentage = data.get("delay_percentage", 0)
    drop = data.get("drop", False)

    if rule_id not in rule_id_map:
        return jsonify({"error": "Rule ID not found"}), 404

    country_code = rule_id_map[rule_id]
    proxy_instance.set_tariff_rule(country_code, delay_percentage, drop)
    save_rules()
    return jsonify({"message": "Rule updated successfully"})


@app.route("/api/rules/<int:rule_id>", methods=["DELETE"])
def delete_rule(rule_id):
    if rule_id not in rule_id_map:
        return jsonify({"error": "Rule ID not found"}), 404

    country_code = rule_id_map.pop(rule_id)
    country_code_map.pop(country_code, None)
    proxy_instance.remove_tariff_rule(country_code)
    save_rules()
    return jsonify({"message": "Rule deleted successfully"})


@app.route("/api/rules", methods=["GET"])
def get_rules():
    rules = []
    for country_code, rule in proxy_instance.get_tariff_rules().items():
        rule_id = country_code_map.get(country_code)
        if rule_id is not None:
            rules.append(
                {
                    "rule_id": rule_id,
                    "country_code": country_code,
                    "delay_percentage": rule.rate,
                    "drop": rule.dropped,
                }
            )
        else:
            print("big trouble")
    return jsonify({"rules": rules})


@app.route("/api/packets", methods=["GET"])
def get_packets():
    packets = []
    for pid, packet in proxy_instance.get_retain_traffic().items():
        packets.append(
            {
                "packet_id": pid,
                "source_ip": packet.from_ip,
                "destination_ip": packet.to_client_ip,
                "source_country": packet.from_country_code,
                "timestamp": packet.recv_time,
                "status": "dropped" if packet.retain_time == 0 else "delayed",
                "applied_rule_id": country_code_map.get(packet.from_country_code),
            }
        )
    print("packets:", jsonify(packets))
    return jsonify({"packets": packets})


load_rules()
