import asyncio
import threading
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.options import Options
from trumproxy import proxy_instance


async def run_proxy():
    opts = Options(
        mode=["wireguard:./wg.conf"],
        listen_host="0.0.0.0",
        listen_port=51820,
    )
    m = DumpMaster(opts, with_termlog=False, with_dumper=False)
    m.addons.add(proxy_instance)

    await m.run()

def control():

    print("Welcome to Trumproxy Control CLI.")
    help_message = """usage:
            rules: show all tariff rules
            retain: show all retained traffic
            set <country> <rate> <is_dropped>: set tariff rule for a country
            remove <country>: remove tariff rule for a country
            exit: exit the control CLI
            help: show this help message"""
    print(help_message)

    while True:
        cmd = input("Enter command: ").strip()
        
        if cmd == "rules":
            map = proxy_instance.get_tariff_rules()
            for country, rule in map.items():
                print(f"{country}: {rule.rate}%, dropped: {rule.dropped}")
        
        elif cmd == "retain":
            traffics = proxy_instance.get_retain_traffic()
            for id, traffic in traffics.items():
                print(f"{id}: {traffic.request_url}, size: {traffic.size} bytes, from: {traffic.from_ip}, to: {traffic.to_client_ip}, rtt: {traffic.rtt_time} ms, retain time: {traffic.retain_time} s")

        elif cmd.startswith("set"):
            try:
                _, country, rate, is_droppped = cmd.split()
                proxy_instance.set_tariff_rule(
                    country,
                    float(rate),
                    is_droppped.lower() == "true",
                )
                print(f"Set {country} tariff to {rate}%, dropped: {is_droppped}")
            except:
                print("Invalid usage.")

        elif cmd.startswith("remove"):
            try:
                _, country = cmd.split()
                proxy_instance.remove_tariff_rule(country)
                print(f"Removed {country} tariff")
            except:
                print("Invalid usage.")
        
        elif cmd == "exit":
            print("Exiting...")
            break

        elif cmd == "help":
            print(help_message)


if __name__ == "__main__":
    control_thread = threading.Thread(target=control)
    control_thread.daemon = True
    control_thread.start()

    asyncio.run(run_proxy())