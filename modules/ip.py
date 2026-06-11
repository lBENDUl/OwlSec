"""
modules/ip.py — Análisis de IPs
Funciones: Geolocalización, Shodan
"""

import requests
from utils.banner import Colors
from utils.logger import get_logger

logger = get_logger()


class IPAnalyzer:

    def __init__(self, target: str):
        self.target = target.strip()
        self.results = {}

    def run(self, geo=False, shodan=False) -> dict:
        print(Colors.section(f"IP: {self.target}"))

        if geo:
            self.results["geo"] = self._geolocate()
        if shodan:
            self.results["shodan"] = self._shodan()

        return self.results

    # ─────────────────────────────────────────────
    # GEOLOCALIZACIÓN (ip-api.com — gratuito)
    # ─────────────────────────────────────────────
    def _geolocate(self) -> dict:
        print(Colors.info("Geolocalizando IP..."))
        try:
            r = requests.get(f"http://ip-api.com/json/{self.target}", timeout=10)
            data = r.json()
            if data.get("status") == "success":
                info = {
                    "country":  data.get("country", "N/A"),
                    "region":   data.get("regionName", "N/A"),
                    "city":     data.get("city", "N/A"),
                    "isp":      data.get("isp", "N/A"),
                    "org":      data.get("org", "N/A"),
                    "lat":      data.get("lat"),
                    "lon":      data.get("lon"),
                    "timezone": data.get("timezone", "N/A"),
                    "as":       data.get("as", "N/A"),
                }
                print(Colors.ok(f"País:      {info['country']}"))
                print(Colors.ok(f"Ciudad:    {info['city']}, {info['region']}"))
                print(Colors.ok(f"ISP:       {info['isp']}"))
                print(Colors.ok(f"ASN:       {info['as']}"))
                print(Colors.ok(f"Coords:    {info['lat']}, {info['lon']}"))
                return info
            else:
                print(Colors.warn(f"ip-api devolvió: {data.get('message', 'error')}"))
                return {"error": data.get("message", "unknown")}
        except Exception as e:
            print(Colors.error(f"Geolocalización fallida: {e}"))
            return {"error": str(e)}

    # ─────────────────────────────────────────────
    # SHODAN (requiere API key en config.yaml)
    # ─────────────────────────────────────────────
    def _shodan(self) -> dict:
        print(Colors.info("Consultando Shodan..."))
        try:
            from utils.config import load_config
            config = load_config()
            api_key = config.get("shodan_api_key")
            if not api_key:
                print(Colors.warn("Shodan: no hay API key configurada en config.yaml"))
                return {"error": "No API key"}

            r = requests.get(
                f"https://api.shodan.io/shodan/host/{self.target}",
                params={"key": api_key},
                timeout=15
            )
            if r.status_code == 200:
                data = r.json()
                info = {
                    "os":       data.get("os", "N/A"),
                    "ports":    data.get("ports", []),
                    "vulns":    list(data.get("vulns", {}).keys()),
                    "hostnames": data.get("hostnames", []),
                    "tags":     data.get("tags", []),
                }
                print(Colors.ok(f"OS:        {info['os']}"))
                print(Colors.ok(f"Puertos:   {info['ports']}"))
                if info["vulns"]:
                    print(Colors.warn(f"CVEs:      {', '.join(info['vulns'][:5])}"))
                return info
            else:
                print(Colors.error(f"Shodan error {r.status_code}: {r.text}"))
                return {"error": r.text}
        except Exception as e:
            print(Colors.error(f"Shodan falló: {e}"))
            return {"error": str(e)}
