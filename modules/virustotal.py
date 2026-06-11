"""
modules/virustotal.py — Análisis con VirusTotal API v3
Soporta: URLs, dominios, IPs y hashes de ficheros

Requiere API key gratuita en: https://www.virustotal.com/gui/join-us
Límite free tier: 4 peticiones/minuto, 500/día
"""

import hashlib
import time
import requests
from utils.banner import Colors
from utils.logger import get_logger
from utils.config import load_config

logger = get_logger()

VT_BASE = "https://www.virustotal.com/api/v3"


class VirusTotalAnalyzer:

    def __init__(self, target: str):
        self.target  = target.strip()
        self.api_key = self._load_key()
        self.results = {}

    # ─────────────────────────────────────────────
    # ENTRADA PRINCIPAL — autodetecta el tipo
    # ─────────────────────────────────────────────

    def run(self, force_type: str = None) -> dict:
        if not self.api_key:
            print(Colors.error("VirusTotal: no hay API key configurada."))
            print(Colors.info("  Consíguela gratis en: https://www.virustotal.com/gui/join-us"))
            print(Colors.info("  Añádela a config.yaml → virustotal_api_key: \"TU_KEY\""))
            return {"error": "No API key"}

        target_type = force_type or self._detect_type()
        print(Colors.section(f"VIRUSTOTAL [{target_type.upper()}]: {self.target}"))

        dispatch = {
            "url":    self._analyze_url,
            "domain": self._analyze_domain,
            "ip":     self._analyze_ip,
            "hash":   self._analyze_hash,
        }

        fn = dispatch.get(target_type)
        if not fn:
            print(Colors.error(f"Tipo no reconocido: {target_type}"))
            print(Colors.info("Tipos válidos: url, domain, ip, hash"))
            return {"error": f"Unknown type: {target_type}"}

        self.results = fn()
        self.results["target"] = self.target
        self.results["type"]   = target_type
        return self.results

    # ─────────────────────────────────────────────
    # ANÁLISIS DE URL
    # ─────────────────────────────────────────────

    def _analyze_url(self) -> dict:
        print(Colors.info("Enviando URL a VirusTotal..."))

        # Primero intentamos obtener análisis existente
        import base64
        url_id = base64.urlsafe_b64encode(self.target.encode()).decode().rstrip("=")

        r = self._get(f"/urls/{url_id}")
        if r is None or r.get("error"):
            # Si no existe, la enviamos para análisis
            print(Colors.info("No hay análisis previo, enviando para escaneo..."))
            submit = self._post("/urls", data={"url": self.target})
            if not submit:
                return {"error": "No se pudo enviar la URL"}
            analysis_id = submit.get("data", {}).get("id", "")
            # Esperamos resultado
            r = self._wait_analysis(analysis_id)
            if not r:
                return {"error": "Timeout esperando resultado"}

        return self._parse_url_domain_result(r)

    # ─────────────────────────────────────────────
    # ANÁLISIS DE DOMINIO
    # ─────────────────────────────────────────────

    def _analyze_domain(self) -> dict:
        print(Colors.info("Consultando dominio en VirusTotal..."))
        r = self._get(f"/domains/{self.target}")
        if not r:
            return {"error": "Sin respuesta de VT"}

        data = r.get("data", {}).get("attributes", {})
        result = self._parse_url_domain_result(r)

        # Info adicional específica de dominios
        result["whois"]        = data.get("whois", "N/A")[:300] if data.get("whois") else "N/A"
        result["registrar"]    = data.get("registrar", "N/A")
        result["creation_date"]= data.get("creation_date", "N/A")
        result["categories"]   = data.get("categories", {})
        result["dns_records"]  = data.get("last_dns_records", [])[:10]

        # Resolucion de IPs históricas
        resolutions = self._get(f"/domains/{self.target}/resolutions")
        if resolutions:
            ips = [
                r2.get("attributes", {}).get("ip_address", "?")
                for r2 in resolutions.get("data", [])[:5]
            ]
            result["resolved_ips"] = ips
            if ips:
                print(Colors.ok(f"IPs históricas: {', '.join(ips)}"))

        return result

    # ─────────────────────────────────────────────
    # ANÁLISIS DE IP
    # ─────────────────────────────────────────────

    def _analyze_ip(self) -> dict:
        print(Colors.info("Consultando IP en VirusTotal..."))
        r = self._get(f"/ip_addresses/{self.target}")
        if not r:
            return {"error": "Sin respuesta de VT"}

        data   = r.get("data", {}).get("attributes", {})
        result = self._parse_url_domain_result(r)

        result["asn"]          = data.get("asn", "N/A")
        result["as_owner"]     = data.get("as_owner", "N/A")
        result["country"]      = data.get("country", "N/A")
        result["network"]      = data.get("network", "N/A")
        result["regional_isp"] = data.get("regional_internet_registry", "N/A")

        if result["country"] != "N/A":
            print(Colors.ok(f"País:     {result['country']}"))
        if result["as_owner"] != "N/A":
            print(Colors.ok(f"AS Owner: {result['as_owner']} (ASN {result['asn']})"))

        # URLs asociadas a esta IP
        urls_assoc = self._get(f"/ip_addresses/{self.target}/urls")
        if urls_assoc:
            urls = [
                u.get("attributes", {}).get("url", "?")
                for u in urls_assoc.get("data", [])[:5]
            ]
            result["associated_urls"] = urls
            if urls:
                print(Colors.warn(f"URLs asociadas ({len(urls)}):"))
                for u in urls:
                    print(f"    {Colors.DIM}→ {u[:80]}{Colors.RESET}")

        return result

    # ─────────────────────────────────────────────
    # ANÁLISIS DE HASH (MD5 / SHA1 / SHA256)
    # ─────────────────────────────────────────────

    def _analyze_hash(self) -> dict:
        print(Colors.info(f"Consultando hash en VirusTotal..."))
        r = self._get(f"/files/{self.target}")
        if not r:
            return {"error": "Hash no encontrado en VT (fichero no conocido)"}

        data   = r.get("data", {}).get("attributes", {})
        stats  = data.get("last_analysis_stats", {})
        total  = sum(stats.values())
        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)

        verdict = self._verdict(malicious, suspicious, total)
        self._print_verdict(verdict, malicious, suspicious, total)

        # Detecciones por motor
        engines = data.get("last_analysis_results", {})
        detections = [
            {"engine": name, "result": info.get("result", ""), "category": info.get("category", "")}
            for name, info in engines.items()
            if info.get("category") in ("malicious", "suspicious")
        ]

        result = {
            "verdict":      verdict,
            "malicious":    malicious,
            "suspicious":   suspicious,
            "undetected":   stats.get("undetected", 0),
            "total_engines":total,
            "detections":   detections,
            "file_name":    data.get("meaningful_name", "N/A"),
            "file_type":    data.get("type_description", "N/A"),
            "file_size":    data.get("size", "N/A"),
            "md5":          data.get("md5", "N/A"),
            "sha1":         data.get("sha1", "N/A"),
            "sha256":       data.get("sha256", "N/A"),
            "first_seen":   data.get("first_submission_date", "N/A"),
            "last_seen":    data.get("last_submission_date", "N/A"),
            "times_submitted": data.get("times_submitted", "N/A"),
            "tags":         data.get("tags", []),
            "vt_link":      f"https://www.virustotal.com/gui/file/{self.target}",
        }

        print(Colors.ok(f"Fichero:   {result['file_name']} ({result['file_type']})"))
        if detections:
            print(Colors.warn(f"Detectado por:"))
            for d in detections[:8]:
                print(f"    {Colors.RED}→{Colors.RESET} {d['engine']:25} {d['result']}")
            if len(detections) > 8:
                print(Colors.warn(f"  ... y {len(detections)-8} motores más"))

        return result

    # ─────────────────────────────────────────────
    # PARSER COMPARTIDO URL / DOMINIO / IP
    # ─────────────────────────────────────────────

    def _parse_url_domain_result(self, r: dict) -> dict:
        data  = r.get("data", {}).get("attributes", {})
        stats = data.get("last_analysis_stats", {})
        total = sum(stats.values())
        malicious  = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)

        verdict = self._verdict(malicious, suspicious, total)
        self._print_verdict(verdict, malicious, suspicious, total)

        engines = data.get("last_analysis_results", {})
        detections = [
            {"engine": name, "result": info.get("result", ""), "category": info.get("category", "")}
            for name, info in engines.items()
            if info.get("category") in ("malicious", "suspicious")
        ]

        result = {
            "verdict":       verdict,
            "malicious":     malicious,
            "suspicious":    suspicious,
            "undetected":    stats.get("undetected", 0),
            "harmless":      stats.get("harmless", 0),
            "total_engines": total,
            "detections":    detections,
            "reputation":    data.get("reputation", "N/A"),
            "last_analysis": data.get("last_analysis_date", "N/A"),
            "vt_link":       f"https://www.virustotal.com/gui/{'url' if 'url' in str(r) else 'domain'}/{self.target}",
        }

        if detections:
            print(Colors.warn(f"Detectado por {len(detections)} motores:"))
            for d in detections[:5]:
                print(f"    {Colors.RED}→{Colors.RESET} {d['engine']:25} {d['result'] or d['category']}")
            if len(detections) > 5:
                print(Colors.warn(f"  ... y {len(detections)-5} más"))
        else:
            print(Colors.ok("Sin detecciones malignas conocidas."))

        return result

    # ─────────────────────────────────────────────
    # HELPERS HTTP
    # ─────────────────────────────────────────────

    def _get(self, endpoint: str) -> dict | None:
        try:
            r = requests.get(
                f"{VT_BASE}{endpoint}",
                headers={"x-apikey": self.api_key},
                timeout=15,
            )
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 404:
                return None
            elif r.status_code == 429:
                print(Colors.warn("Rate limit alcanzado. Esperando 60s..."))
                time.sleep(60)
                return self._get(endpoint)
            else:
                print(Colors.error(f"VT HTTP {r.status_code}: {r.text[:100]}"))
                return None
        except Exception as e:
            print(Colors.error(f"Error de conexión: {e}"))
            return None

    def _post(self, endpoint: str, data: dict) -> dict | None:
        try:
            r = requests.post(
                f"{VT_BASE}{endpoint}",
                headers={"x-apikey": self.api_key},
                data=data,
                timeout=15,
            )
            return r.json() if r.status_code in (200, 201) else None
        except Exception as e:
            print(Colors.error(f"Error POST: {e}"))
            return None

    def _wait_analysis(self, analysis_id: str, max_wait: int = 60) -> dict | None:
        """Espera hasta que el análisis esté listo (máx max_wait segundos)."""
        print(Colors.info("Esperando resultado del análisis", ), end="", flush=True)
        for _ in range(max_wait // 5):
            time.sleep(5)
            print(".", end="", flush=True)
            r = self._get(f"/analyses/{analysis_id}")
            if r:
                status = r.get("data", {}).get("attributes", {}).get("status", "")
                if status == "completed":
                    print(" ✓")
                    # Devolvemos el análisis de la URL original
                    import base64
                    url_id = base64.urlsafe_b64encode(self.target.encode()).decode().rstrip("=")
                    return self._get(f"/urls/{url_id}")
        print(" timeout")
        return None

    # ─────────────────────────────────────────────
    # DETECCIÓN AUTOMÁTICA DE TIPO
    # ─────────────────────────────────────────────

    def _detect_type(self) -> str:
        import re
        t = self.target

        # Hash: MD5 (32), SHA1 (40), SHA256 (64) — solo hex
        if re.fullmatch(r"[a-fA-F0-9]{32}|[a-fA-F0-9]{40}|[a-fA-F0-9]{64}", t):
            return "hash"

        # IP v4
        if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", t):
            return "ip"

        # URL (empieza con http/https)
        if t.startswith("http://") or t.startswith("https://"):
            return "url"

        # Por defecto: dominio
        return "domain"

    # ─────────────────────────────────────────────
    # VEREDICTO Y CARGA DE KEY
    # ─────────────────────────────────────────────

    def _verdict(self, malicious: int, suspicious: int, total: int) -> str:
        if total == 0:
            return "unknown"
        if malicious >= 3:
            return "malicious"
        if malicious >= 1 or suspicious >= 3:
            return "suspicious"
        return "clean"

    def _print_verdict(self, verdict: str, malicious: int, suspicious: int, total: int):
        icons = {
            "malicious":  f"{Colors.RED}🔴 MALICIOSO",
            "suspicious": f"{Colors.YELLOW}🟡 SOSPECHOSO",
            "clean":      f"{Colors.GREEN}🟢 LIMPIO",
            "unknown":    f"{Colors.DIM}⚪ DESCONOCIDO",
        }
        label = icons.get(verdict, "❓")
        print(f"\n  Veredicto: {Colors.BOLD}{label}{Colors.RESET}")
        print(Colors.ok(f"Motores:   {malicious} malicioso / {suspicious} sospechoso / {total} total\n"))

    def _load_key(self) -> str:
        config = load_config()
        key = config.get("virustotal_api_key", "").strip()
        return key
