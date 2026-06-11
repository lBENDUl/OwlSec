"""
modules/domain.py — Análisis de dominios
Funciones: WHOIS, DNS, Subdominios (crt.sh)
"""

import socket
import requests
import dns.resolver
import whois as python_whois
from utils.banner import Colors
from utils.logger import get_logger

logger = get_logger()


class DomainAnalyzer:

    def __init__(self, target: str):
        self.target = target.strip().lower().removeprefix("http://").removeprefix("https://").split("/")[0]
        self.results = {}

    def run(self, whois=False, dns=False, subdomains=False) -> dict:
        print(Colors.section(f"DOMINIO: {self.target}"))

        if whois:
            self.results["whois"] = self._whois()
        if dns:
            self.results["dns"] = self._dns()
        if subdomains:
            self.results["subdomains"] = self._subdomains_crtsh()

        return self.results

    # ─────────────────────────────────────────────
    # WHOIS
    # ─────────────────────────────────────────────
    def _whois(self) -> dict:
        print(Colors.info("Consultando WHOIS..."))
        try:
            w = python_whois.whois(self.target)
            data = {
                "registrar":       str(w.registrar or "N/A"),
                "creation_date":   str(w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date or "N/A"),
                "expiration_date": str(w.expiration_date[0] if isinstance(w.expiration_date, list) else w.expiration_date or "N/A"),
                "name_servers":    w.name_servers or [],
                "emails":          w.emails or [],
                "country":         str(w.country or "N/A"),
                "org":             str(w.org or "N/A"),
            }
            print(Colors.ok(f"Registrador:   {data['registrar']}"))
            print(Colors.ok(f"Creación:      {data['creation_date']}"))
            print(Colors.ok(f"Expiración:    {data['expiration_date']}"))
            print(Colors.ok(f"Organización:  {data['org']}"))
            print(Colors.ok(f"País:          {data['country']}"))
            return data
        except Exception as e:
            print(Colors.error(f"WHOIS fallido: {e}"))
            return {"error": str(e)}

    # ─────────────────────────────────────────────
    # DNS
    # ─────────────────────────────────────────────
    def _dns(self) -> dict:
        print(Colors.info("Enumerando registros DNS..."))
        record_types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]
        data = {}

        for rtype in record_types:
            try:
                answers = dns.resolver.resolve(self.target, rtype, lifetime=5)
                records = [r.to_text() for r in answers]
                data[rtype] = records
                print(Colors.ok(f"{rtype:6} → {', '.join(records[:3])}{'...' if len(records) > 3 else ''}"))
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                pass
            except Exception:
                pass

        return data

    # ─────────────────────────────────────────────
    # SUBDOMINIOS via crt.sh
    # ─────────────────────────────────────────────
    def _subdomains_crtsh(self) -> list:
        print(Colors.info("Buscando subdominios en crt.sh..."))
        subdomains = set()
        try:
            url = f"https://crt.sh/?q=%.{self.target}&output=json"
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                for entry in data:
                    name = entry.get("name_value", "")
                    for sub in name.split("\n"):
                        sub = sub.strip().lower()
                        if sub.endswith(self.target) and "*" not in sub:
                            subdomains.add(sub)

            subdomains = sorted(subdomains)
            print(Colors.ok(f"Subdominios encontrados: {len(subdomains)}"))
            for sub in subdomains[:10]:
                print(f"    {Colors.GREEN}→{Colors.RESET} {sub}")
            if len(subdomains) > 10:
                print(Colors.info(f"  ... y {len(subdomains) - 10} más (ver informe completo)"))
        except Exception as e:
            print(Colors.error(f"crt.sh falló: {e}"))

        return list(subdomains)
