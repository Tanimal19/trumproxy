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
    while True:
        cmd = input("Enter command: ").strip()
        
        if cmd == "get tariff":
            map = proxy_instance.get_tariff_map()
            for k, v in map.items():
                print(f"{k}: {v}%")
        
        if cmd == "get retain":
            traffics = proxy_instance.get_retain_traffic()
            for k, v in traffics.items():
                print(f"{k}: {v}")

        elif cmd.startswith("set"):
            try:
                _, country, tariff = cmd.split()
                print(f"Set {tariff}% tariff on {country}.")
                proxy_instance.set_tariff_for_country(country, int(tariff))
            except:
                print("Invalid usage.")

        elif cmd.startswith("remove"):
            try:
                _, country = cmd.split()
                print(f"Remove tariff on {country}.")
                proxy_instance.remove_tariff_for_country(country)
            except:
                print("Invalid usage.")
        
        elif cmd == "exit":
            print("Exiting...")
            break
        
        else:
            print("Unknown command.")


if __name__ == "__main__":
    control_thread = threading.Thread(target=control)
    control_thread.daemon = True
    control_thread.start()

    asyncio.run(run_proxy())