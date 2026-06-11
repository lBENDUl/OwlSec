"""
modules/email_check.py — Análisis de emails
Funciones: Validación, MX check, Have I Been Pwned
"""

import re
import requests
import dns.resolver
from utils.banner import Colors
from utils.logger import get_logger

logger = get_logger()

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class EmailAnalyzer:

    def __init__(self, target: str):
        self.target = target.strip().lower()
        self.results = {}

    def run(self, validate=False, hibp=False) -> dict:
        print(Colors.section(f"EMAIL: {self.target}"))

        if validate:
            self.results["validation"] = self._validate()
        if hibp:
            self.results["hibp"] = self._hibp()

        return self.results

    # ─────────────────────────────────────────────
    # VALIDACIÓN (formato + registros MX)
    # ─────────────────────────────────────────────
    def _validate(self) -> dict:
        print(Colors.info("Validando email..."))
        data = {"email": self.target, "format_valid": False, "mx_valid": False, "mx_records": []}

        # Formato
        if EMAIL_REGEX.match(self.target):
            data["format_valid"] = True
            print(Colors.ok("Formato válido"))
        else:
            print(Colors.error("Formato inválido"))
            return data

        # MX del dominio
        domain = self.target.split("@")[1]
        try:
            mx_records = dns.resolver.resolve(domain, "MX", lifetime=5)
            data["mx_records"] = sorted([r.exchange.to_text() for r in mx_records])
            data["mx_valid"] = True
            print(Colors.ok(f"Registros MX: {', '.join(data['mx_records'][:3])}"))
        except Exception as e:
            print(Colors.warn(f"No se encontraron registros MX: {e}"))

        return data

    # ─────────────────────────────────────────────
    # HAVE I BEEN PWNED
    # ─────────────────────────────────────────────
    def _hibp(self) -> dict:
        print(Colors.info("Consultando Have I Been Pwned..."))
        try:
            from utils.config import load_config
            config = load_config()
            api_key = config.get("hibp_api_key", "")

            headers = {"hibp-api-key": api_key, "User-Agent": "osint-toolkit"} if api_key else {"User-Agent": "osint-toolkit"}
            r = requests.get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{self.target}",
                headers=headers,
                timeout=10
            )
            if r.status_code == 200:
                breaches = r.json()
                names = [b.get("Name", "?") for b in breaches]
                print(Colors.warn(f"¡Encontrado en {len(names)} brechas!"))
                for name in names:
                    print(f"    {Colors.RED}→{Colors.RESET} {name}")
                return {"breached": True, "count": len(names), "breaches": names}
            elif r.status_code == 404:
                print(Colors.ok("No encontrado en ninguna brecha conocida"))
                return {"breached": False, "count": 0, "breaches": []}
            elif r.status_code == 401:
                print(Colors.warn("HIBP requiere API key (v3). Configúrala en config.yaml"))
                return {"error": "API key requerida"}
            else:
                print(Colors.error(f"HIBP error {r.status_code}"))
                return {"error": f"HTTP {r.status_code}"}
        except Exception as e:
            print(Colors.error(f"HIBP falló: {e}"))
            return {"error": str(e)}
