"""
modules/dorks.py — Google Dorks Generator
Genera dorks categorizados y abre búsquedas en el navegador.

IMPORTANTE: Esta herramienta NO hace scraping de Google (viola sus ToS).
Genera las URLs de búsqueda para que el usuario las ejecute manualmente
o las abra directamente en el navegador.
"""

import webbrowser
import urllib.parse
from utils.banner import Colors
from utils.logger import get_logger

logger = get_logger()

# ─────────────────────────────────────────────────────────────────────────────
# CATÁLOGO DE DORKS por categoría
# Cada dork usa {target} como placeholder del dominio/objetivo
# ─────────────────────────────────────────────────────────────────────────────

DORKS_CATALOG = {

    "📂 Exposición de archivos": [
        ('Documentos sensibles (PDF, DOC, XLS)',
         'site:{target} ext:pdf OR ext:doc OR ext:xls OR ext:xlsx'),
        ('Archivos de configuración',
         'site:{target} ext:xml OR ext:conf OR ext:config OR ext:ini'),
        ('Ficheros de backup',
         'site:{target} ext:bak OR ext:old OR ext:backup OR ext:sql'),
        ('Logs expuestos',
         'site:{target} ext:log'),
        ('Archivos comprimidos públicos',
         'site:{target} ext:zip OR ext:tar OR ext:gz OR ext:rar'),
    ],

    "🔐 Credenciales y datos sensibles": [
        ('Contraseñas en texto plano',
         'site:{target} intext:password OR intext:passwd OR intext:pwd'),
        ('Claves API expuestas',
         'site:{target} intext:"api_key" OR intext:"api_secret" OR intext:"access_token"'),
        ('Credenciales en URLs',
         'site:{target} inurl:password OR inurl:passwd OR inurl:credentials'),
        ('Archivos .env expuestos',
         'site:{target} ext:env OR inurl:.env'),
        ('Tokens y secretos en código',
         'site:{target} intext:"secret_key" OR intext:"private_key" OR intext:"client_secret"'),
    ],

    "🗂️ Paneles de administración": [
        ('Panel de admin genérico',
         'site:{target} inurl:admin OR inurl:administrator OR inurl:wp-admin'),
        ('Páginas de login',
         'site:{target} inurl:login OR inurl:signin OR inurl:auth'),
        ('Paneles de control',
         'site:{target} inurl:dashboard OR inurl:panel OR inurl:control'),
        ('phpMyAdmin',
         'site:{target} inurl:phpmyadmin'),
        ('Consolas de gestión',
         'site:{target} inurl:manager OR inurl:management OR inurl:console'),
    ],

    "⚙️ Tecnología y stack": [
        ('Errores PHP expuestos',
         'site:{target} "PHP Parse error" OR "PHP Warning" OR "PHP Fatal error"'),
        ('Stack traces visibles',
         'site:{target} "stack trace" OR "Traceback" OR "at line" filetype:html'),
        ('Páginas de error con info técnica',
         'site:{target} intext:"SQL syntax" OR intext:"mysql_fetch" OR intext:"ORA-"'),
        ('Instalaciones WordPress',
         'site:{target} inurl:wp-content OR inurl:wp-includes'),
        ('Versiones de software expuestas',
         'site:{target} intext:"powered by" OR intext:"running on" OR intext:"version"'),
    ],

    "📁 Directorios y rutas": [
        ('Directory listing habilitado',
         'site:{target} intitle:"index of" OR intitle:"directory listing"'),
        ('Rutas internas expuestas',
         'site:{target} inurl:/internal/ OR inurl:/private/ OR inurl:/secret/'),
        ('Carpetas de uploads',
         'site:{target} intitle:"index of" inurl:uploads OR inurl:files OR inurl:media'),
        ('Repositorios git expuestos',
         'site:{target} inurl:.git OR intitle:"index of /.git"'),
        ('Archivos htaccess/htpasswd',
         'site:{target} inurl:.htaccess OR inurl:.htpasswd'),
    ],

    "📧 Información personal y contacto": [
        ('Emails del dominio',
         'site:{target} intext:"@{target}"'),
        ('Números de teléfono',
         'site:{target} intext:"tel:" OR intext:"phone:" OR intext:"+34"'),
        ('Documentos con nombres de empleados',
         'site:{target} filetype:pdf intext:"curriculum" OR intext:"resume" OR intext:"cv"'),
    ],

    "🔍 Subdominios y infraestructura": [
        ('Subdominios indexados',
         'site:*.{target} -www'),
        ('Servicios internos expuestos',
         'site:{target} inurl:dev OR inurl:staging OR inurl:test OR inurl:beta'),
        ('APIs expuestas',
         'site:{target} inurl:api OR inurl:/v1/ OR inurl:/v2/ OR inurl:swagger'),
        ('Documentación técnica',
         'site:{target} inurl:docs OR inurl:wiki OR inurl:confluence'),
    ],

    "🗄️ Bases de datos": [
        ('Dumps SQL expuestos',
         'site:{target} ext:sql intext:"INSERT INTO" OR intext:"CREATE TABLE"'),
        ('MongoDB expuesto',
         'site:{target} inurl:27017 OR inurl:mongodb'),
        ('Ficheros de base de datos',
         'site:{target} ext:db OR ext:sqlite OR ext:mdb'),
    ],
}

# ─────────────────────────────────────────────────────────────────────────────

class DorksAnalyzer:

    GOOGLE_BASE = "https://www.google.com/search?q="
    BING_BASE   = "https://www.bing.com/search?q="

    def __init__(self, target: str):
        self.target = target.strip().lower().removeprefix("http://").removeprefix("https://").split("/")[0]
        self.results = {}

    def run(self,
            categories: list = None,
            engine: str = "google",
            open_browser: bool = False,
            list_only: bool = False) -> dict:

        print(Colors.section(f"GOOGLE DORKS: {self.target}"))

        all_dorks = self._build_dorks(categories)
        self.results = {
            "target":     self.target,
            "engine":     engine,
            "total":      sum(len(v) for v in all_dorks.values()),
            "categories": {},
        }

        for category, dorks in all_dorks.items():
            print(f"\n  {Colors.BOLD}{Colors.MAGENTA}{category}{Colors.RESET}")
            cat_data = []

            for name, dork_query in dorks:
                query    = dork_query.replace("{target}", self.target)
                url      = self._build_url(query, engine)
                cat_data.append({"name": name, "query": query, "url": url})

                if list_only:
                    print(f"  {Colors.DIM}  {name}{Colors.RESET}")
                    print(f"    {Colors.CYAN}{query}{Colors.RESET}")
                else:
                    print(f"  {Colors.ok(name)}")
                    print(f"    {Colors.DIM}{url[:90]}...{Colors.RESET}" if len(url) > 90 else f"    {Colors.DIM}{url}{Colors.RESET}")

                if open_browser:
                    webbrowser.open(url)

            self.results["categories"][category] = cat_data

        self._print_summary(open_browser)
        return self.results

    def run_custom(self, custom_query: str, engine: str = "google") -> dict:
        """Ejecuta un dork personalizado."""
        print(Colors.section(f"DORK PERSONALIZADO: {self.target}"))
        query = custom_query.replace("{target}", self.target)
        url   = self._build_url(query, engine)

        print(Colors.ok(f"Query: {query}"))
        print(Colors.info(f"URL:   {url}"))

        self.results = {
            "target":  self.target,
            "type":    "custom",
            "query":   query,
            "url":     url,
            "engine":  engine,
        }
        return self.results

    # ─────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────

    def _build_dorks(self, categories: list) -> dict:
        if not categories:
            return DORKS_CATALOG
        return {k: v for k, v in DORKS_CATALOG.items()
                if any(cat.lower() in k.lower() for cat in categories)}

    def _build_url(self, query: str, engine: str) -> str:
        encoded = urllib.parse.quote_plus(query)
        base    = self.BING_BASE if engine == "bing" else self.GOOGLE_BASE
        return f"{base}{encoded}"

    def _print_summary(self, opened: bool):
        total = self.results.get("total", 0)
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'─'*50}{Colors.RESET}")
        print(Colors.ok(f"Total dorks generados: {Colors.BOLD}{total}{Colors.RESET}"))
        if opened:
            print(Colors.warn("Se han abierto las búsquedas en el navegador."))
            print(Colors.warn("Google puede solicitar CAPTCHA si abres muchas a la vez."))
        else:
            print(Colors.info("Usa --open para abrir las búsquedas en el navegador."))
            print(Colors.info("Usa --report para exportar todas las URLs a HTML."))


def list_categories():
    """Imprime las categorías disponibles."""
    print(Colors.section("CATEGORÍAS DE DORKS DISPONIBLES"))
    for i, cat in enumerate(DORKS_CATALOG.keys(), 1):
        count = len(DORKS_CATALOG[cat])
        print(f"  {Colors.CYAN}{i:2}.{Colors.RESET} {cat} {Colors.DIM}({count} dorks){Colors.RESET}")
