# type: ignore

import asyncio
from dataclasses import dataclass
from mitmproxy import http
import geoip2.database

GEOIP_DB_PATH = "./GeoLite2-Country.mmdb"

@dataclass
class TariffRule:
    rate: int
    """
    The rate of the tariff to calculate retain_time (in seconds).\n
    retain_time = rtt_time * (rate).\n
    0-100.
    """

    dropped: bool
    """
    To drop the traffic or not. If True, the rate is ignored.
    """


@dataclass
class Packet:
    request_url: str
    """
    The url being request.
    """

    size: int
    """
    The size of the response.
    """

    from_ip: str
    """
    The IP address of the server.
    """

    from_country_code: str
    """
    The country code of the server.
    """

    recv_time: int
    """
    The time when the response was received. (milliseconds since epoch)
    """

    rtt_time: float
    """
    The round trip time of the request in milliseconds.
    """

    retain_time: float | None
    """
    The time to retain the response in seconds. (None if dropped)
    """

    status: str
    """
    The status of the response. (dropped or retained)
    """



class TrumproxyAddon:
    def __init__(self):
        self.tariff_rules: dict[str, TariffRule] = {}
        self.cache_packets: dict[str, Packet] = {}
        self.geo_identifier = geoip2.database.Reader(GEOIP_DB_PATH)

        print("Trumproxy started.")

    def response(self, flow: http.HTTPFlow):
        try:
            from_ip = flow.server_conn.peername[0]
            country = self.geo_identifier.country(from_ip)
            from_country_code = country.country.iso_code

            print(
                f"[{flow.id}] Get response from {flow.request.pretty_url} from {from_ip}"
            )

            if from_country_code is None:
                print(f"[{flow.id}] No country code found")
                return

            if from_country_code not in self.tariff_rules:
                print(
                    f"[{flow.id}] Pass packet since no tariff rule on {from_country_code}"
                )
                return

            rule: TariffRule = self.tariff_rules[from_country_code]

            if rule.dropped:
                self.cache_packets[flow.id] = Packet(
                    request_url=flow.request.pretty_url,
                    size=len(flow.response.content),
                    from_ip=from_ip,
                    from_country_code=from_country_code,
                    recv_time=int(flow.response.timestamp_end * 1000),
                    rtt_time=flow.response.timestamp_end - flow.request.timestamp_start,
                    retain_time=None,
                    status="dropped",
                )
                print(f"[{flow.id}] Drop packet from {from_country_code}")
                flow.kill()
                return

            rtt_time = flow.response.timestamp_end - flow.request.timestamp_start
            retain_time = rtt_time * (rule.rate)
            print(
                f"[{flow.id}] Retain packet from {from_country_code} for {retain_time}s"
            )

            self.cache_packets[flow.id] = Packet(
                request_url=flow.request.pretty_url,
                size=len(flow.response.content),
                from_ip=from_ip,
                from_country_code=from_country_code,
                recv_time=int(flow.response.timestamp_end * 1000),
                rtt_time=rtt_time,
                retain_time=retain_time,
                status="retained",
            )

            asyncio.create_task(self.retain_flow(flow, retain_time))
            flow.intercept()

        except Exception as e:
            print(f"[{flow.id}] Error: {e}")

    def done(self):
        self.geo_identifier.close()
        self.cache_packets.clear()
        self.tariff_rules.clear()
        print("Trumproxy closed.")

    async def retain_flow(self, flow: http.HTTPFlow, retain_time: float):
        await asyncio.sleep(retain_time)
        if flow.response:
            print(f"[{flow.id}] Release packet")
            self.cache_packets.pop(flow.id, None)
            flow.resume()

    # for API control
    def get_tariff_rules(self) -> dict[str, TariffRule]:
        """
        Get all tariff rules.
        """
        print("get_tariff_rules()")
        return self.tariff_rules

    def set_tariff_rule(self, iso_code, tariff, dropped=False):
        """
        Set the tariff rule for the given country code. (Overwrite if exists)

        Params:
            iso_code (str): The ISO 3166-1 alpha-2 country code.
            tariff (int): The tariff rate (0-100).
            dropped (bool): Whether to drop the traffic or not.
        """
        print(f"set_tariff_rule({iso_code}, {tariff}, {dropped})")
        self.tariff_rules[iso_code.upper()] = TariffRule(rate=tariff, dropped=dropped)

    def remove_tariff_rule(self, iso_code):
        """
        Remove the tariff rule for the given country code.

        Params:
            iso_code (str): The ISO 3166-1 alpha-2 country code.
        """
        print(f"remove_tariff_rule({iso_code})")
        if iso_code in self.tariff_rules:
            self.tariff_rules.pop(iso_code.upper(), None)

    def get_cached_packets(self) -> dict[str, Packet]:
        """
        Get current cached packets. (include retained and dropped)
        """
        return self.cache_packets

    def clean_cached_packets(self):
        """
        Clean the cached packets.
        """
        self.cache_packets.clear()


proxy_instance = TrumproxyAddon()
