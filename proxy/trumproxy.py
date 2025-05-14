import geoip2.database
import geoip2.errors
import asyncio

from mitmproxy import http, options
from mitmproxy.tools import dump


GEOIP_DB_PATH = "./GeoLite2-Country.mmdb"

class Trumproxy:
    def __init__(self):
        self.geo_identifier = geoip2.database.Reader(GEOIP_DB_PATH)

    def request(self, flow: http.HTTPFlow):
        pass
        # ip = flow.server_conn.peername[0]
        # try:
        #     response = self.geo_identifier.country(ip)
        #     country = response.country.name
        #     country_code = response.country.iso_code
        #     print(f"{flow.request.pretty_url} from {ip} ({country} {country_code})")
        # except geoip2.errors.AddressNotFoundError:
        #     print(f"Can identify country for {ip} ")
        # except Exception as e:
        #     print(f"Error: {e}")


async def start_mitm():
    opts = options.Options(
        mode=["wireguard:./conf/wireguard.conf"],
        listen_host="0.0.0.0",
        listen_port=51820,
    )

    master = dump.DumpMaster(opts, with_termlog=True, with_dumper=True)
    master.addons.add(Trumproxy())

    try:
        print("Starting mitmproxy...")
        await master.run()
    except asyncio.exceptions.CancelledError or KeyboardInterrupt:
        print("Stopping mitmproxy...")

if __name__ == "__main__":
    asyncio.run(start_mitm())
