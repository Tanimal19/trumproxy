import logging
from mitmproxy import http
import geoip2.database
import geoip2.errors
import asyncio

# logging.basicConfig(filename='trumproxy.log', level=logging.info,
#                     format='%(asctime)s - %(levelname)s - %(message)s')

GEOIP_DB_PATH = "./GeoLite2-Country.mmdb"



class TrumproxyAddon:
    def __init__(self):
        self.tariff_map = {}
        self.retain_traffic = {}
        self.geo_identifier = geoip2.database.Reader(GEOIP_DB_PATH)
        self.f = open("trumproxy.log", "w", 1)

    def request(self, flow: http.HTTPFlow):
        packet_url = flow.request.pretty_url
        dst_ip = flow.server_conn.peername[0]

        try:
            dst_location = self.geo_identifier.country(dst_ip)
            iso_code = dst_location.country.iso_code
            
            self.f.write(f"[PASS] {packet_url} from {dst_ip} (country: {iso_code})\n")

            if iso_code in self.tariff_map:
                tariff = self.tariff_map[iso_code]
                self.f.write(f"[TARIFF] {dst_ip} tariffed for {tariff}s\n")
                asyncio.create_task(self.tariffed_resume(flow, tariff))

                self.retain_traffic[flow.id] = {
                    "url": packet_url,
                    "ip": dst_ip,
                    "country": iso_code,
                }

                flow.intercept()

        except Exception as e:
            logging.error(f"Error: {e}")

    def done(self):
        self.f.close()

    async def tariffed_resume(self, flow: http.HTTPFlow, tariff: int):
        await asyncio.sleep(tariff)
        if not flow.response:
            self.retain_traffic.pop(flow.id, None)
            flow.resume()

    # for API control
    def get_tariff_map(self):
        return self.tariff_map
    
    def get_retain_traffic(self):
        return self.retain_traffic

    def set_tariff_for_country(self, iso_code, tariff):
        self.tariff_map[iso_code] = tariff

    def remove_tariff_for_country(self, iso_code):
        if iso_code in self.tariff_map:
            self.tariff_map.pop(iso_code)


proxy_instance = TrumproxyAddon()

