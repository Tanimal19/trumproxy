# type: ignore

import logging
import asyncio
from dataclasses import dataclass
import time
from mitmproxy import http
import geoip2.database
import geoip2.errors

# logging.basicConfig(filename='trumproxy.log', level=logging.info,
#                     format='%(asctime)s - %(levelname)s - %(message)s')

GEOIP_DB_PATH = "./GeoLite2-Country.mmdb"


@dataclass
class TariffRule:
    rate: int
    """
    The rate of the tariff to calculate retain_time.\n
    retain_time = rtt_time * (rate / 100).\n
    0-100.
    """

    dropped: bool
    """
    To drop the traffic or not. If True, the rate is ignored.
    """


@dataclass
class RetainedResponse:
    """
    A retained response.
    """

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

    to_client_ip: str
    """
    The IP address of the client.
    """

    recv_time: float
    """
    The time when the response was received.
    """

    rtt_time: float
    """
    The round trip time of the request.
    """

    retain_time: float
    """
    The time to retain the response.
    """


class TrumproxyAddon:
    def __init__(self):
        self.tariff_rules: dict[str, TariffRule] = {}
        self.retain_responses: dict[str, RetainedResponse] = {}

        self.geo_identifier = geoip2.database.Reader(GEOIP_DB_PATH)
        self.f = open("trumproxy.log", "w", 1)

    def response(self, flow: http.HTTPFlow):
        try:
            from_ip = flow.server_conn.peername[0]
            country = self.geo_identifier.country(from_ip)
            from_country_code = country.country.iso_code

            to_ip = flow.client_conn.peername[0]

            if from_country_code is None:
                self.f.write(f"[ERROR] No country code for {from_ip}\n")
                return

            if from_country_code not in self.tariff_rules:
                self.f.write(
                    f"[PASS] No tariff for {from_ip} (country: {from_country_code})\n"
                )
                return

            rule: TariffRule = self.tariff_rules[from_country_code]

            if rule.dropped:
                self.f.write(f"[DROP] {from_ip} (country: {from_country_code})\n")
                flow.kill()
                return

            rtt_time = flow.response.timestamp_end - flow.request.timestamp_start
            retain_time = rtt_time * (rule.rate)
            self.f.write(
                f"[RETAIN] {from_ip} (country: {from_country_code}) for {retain_time}ms\n"
            )

            self.retain_responses[flow.id] = RetainedResponse(
                request_url=flow.request.pretty_url,
                size=len(flow.response.content),
                from_ip=from_ip,
                from_country_code=from_country_code,
                to_client_ip=to_ip,
                recv_time=flow.response.timestamp_end,
                rtt_time=rtt_time,
                retain_time=retain_time,
            )

            asyncio.create_task(self.tariffed_resume(flow, retain_time))
            flow.intercept()

        except Exception as e:
            self.f.write(f"[Error] {e}")

    def done(self):
        self.f.close()

    async def retain_flow(self, flow: http.HTTPFlow, retain_time: float):
        await asyncio.sleep(retain_time)
        if not flow.response:
            self.retain_responses.pop(flow.id, None)
            flow.resume()

    # for API control
    def get_tariff_rules(self) -> dict[str, TariffRule]:
        """
        Get all tariff rules.
        """
        return self.tariff_rules

    def get_retain_traffic(self) -> dict[str, RetainedResponse]:
        """
        Get the retained traffic.
        """
        return self.retain_responses

    def set_tariff_rule(self, iso_code, tariff, dropped=False):
        """
        Set the tariff rule for the given country code.
        :param iso_code: The ISO 3166-1 alpha-2 country code.
        :param tariff: The tariff rate (0-100).
        :param dropped: Whether to drop the traffic or not.
        """
        iso_code = iso_code.upper()
        self.tariff_rules.setdefault(iso_code, TariffRule(rate=tariff, dropped=dropped))

    def remove_tariff_rule(self, iso_code):
        """
        Remove the tariff rule for the given country code.
        :param iso_code: The ISO 3166-1 alpha-2 country code.
        """
        iso_code = iso_code.upper()
        if iso_code in self.tariff_rules:
            self.tariff_rules.pop(iso_code)


proxy_instance = TrumproxyAddon()
