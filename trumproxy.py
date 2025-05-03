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
        ip = flow.server_conn.peername[0]
        try:
            response = self.geo_identifier.country(ip)
            country = response.country.name
            country_code = response.country.iso_code
            print(f"來自 {ip} ({country} {country_code}）的請求已被記錄。")
        except geoip2.errors.AddressNotFoundError:
            print(f"IP {ip} 無法辨識國家。")
        except Exception as e:
            print(f"處理 IP {ip} 發生錯誤: {e}")


async def start_mitm():
    opts = options.Options(
        mode=["local"], # local capture mode
    )

    master = dump.DumpMaster(opts, with_termlog=False, with_dumper=False)
    master.addons.add(Trumproxy())

    try:
        print("Starting mitmproxy...")
        await master.run()
    except asyncio.exceptions.CancelledError or KeyboardInterrupt:
        print("Stopping mitmproxy...")

if __name__ == "__main__":
    asyncio.run(start_mitm())
