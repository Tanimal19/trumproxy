import asyncio
import threading
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.options import Options
from trumproxy import proxy_instance
from flask_app import app


def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=False)


# CLI currently deprecated, update later if I have time
# def control():
#     print("Welcome to Trumproxy Control CLI.")
#     help_message = """usage:
#         rules: show all tariff rules
#         retain: show all retained traffic
#         set <country> <rate> <is_dropped>: set tariff rule for a country
#         remove <country>: remove tariff rule for a country
#         exit: exit the control CLI
#         help: show this help message"""
#     print(help_message)

#     while True:
#         try:
#             cmd = input("Enter command: ").strip()
#             if cmd == "rules":
#                 rules = proxy_instance.get_tariff_rules()
#                 for country, rule in rules.items():
#                     print(f"{country}: {rule.rate}%, dropped: {rule.dropped}")
#             elif cmd == "retain":
#                 traffic = proxy_instance.get_retain_traffic()
#                 for id, t in traffic.items():
#                     print(
#                         f"{id}: {t.request_url}, size: {t.size} bytes, from: {t.from_ip}, rtt: {t.rtt_time} ms, retain time: {t.retain_time} s"
#                     )
#             elif cmd.startswith("set"):
#                 _, country, rate, dropped = cmd.split()
#                 proxy_instance.set_tariff_rule(
#                     country, int(rate), dropped.lower() == "true"
#                 )
#                 save_rules()
#                 print(f"Set rule: {country} -> {rate}%, dropped: {dropped}")
#             elif cmd.startswith("remove"):
#                 _, country = cmd.split()
#                 proxy_instance.remove_tariff_rule(country)
#                 save_rules()
#                 print(f"Removed rule for {country}")
#             elif cmd == "exit":
#                 print("Exiting CLI...")
#                 break
#             elif cmd == "help":
#                 print(help_message)
#             else:
#                 print("Unknown command. Type 'help' for usage.")
#         except Exception as e:
#             print(f"[Error] {e}")


async def run_proxy():
    opts = Options(
        mode=["wireguard:./wg.conf"],
        listen_host="0.0.0.0",
        listen_port=51820,
    )
    m = DumpMaster(opts, with_termlog=False, with_dumper=False)
    m.addons.add(proxy_instance)

    await m.run()


if __name__ == "__main__":
    # Start Flask in a thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Start CLI in a thread
    # cli_thread = threading.Thread(target=control)
    # cli_thread.daemon = True
    # cli_thread.start()

    # Start mitmproxy in asyncio main loop
    try:
        asyncio.run(run_proxy())
    except KeyboardInterrupt:
        print("Shutting down...")
        proxy_instance.done()
