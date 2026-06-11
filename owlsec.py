#!/usr/bin/env python3
"""
OwlSec - OSINT Toolkit CLI
Autor: tu-nombre
GitHub: github.com/tu-usuario/owlsec
"""

import argparse
import sys
from utils.banner import print_banner
from utils.logger import get_logger

logger = get_logger()


def main():
    print_banner()

    parser = argparse.ArgumentParser(
        prog="owlsec",
        description="OwlSec — OSINT Toolkit · Recopilación pasiva de información",
        formatter_class=argparse.RawTextHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="module", help="Módulo a ejecutar")

    # --- Módulo: domain ---
    domain_parser = subparsers.add_parser("domain", help="Analiza un dominio")
    domain_parser.add_argument("target", help="Dominio objetivo (ej: ejemplo.com)")
    domain_parser.add_argument("--whois",      action="store_true", help="Información WHOIS")
    domain_parser.add_argument("--dns",        action="store_true", help="Enumeración DNS")
    domain_parser.add_argument("--subdomains", action="store_true", help="Descubrimiento de subdominios (crt.sh)")
    domain_parser.add_argument("--all",        action="store_true", help="Ejecutar todos los análisis")
    domain_parser.add_argument("--report",     action="store_true", help="Generar informe HTML")

    # --- Módulo: ip ---
    ip_parser = subparsers.add_parser("ip", help="Analiza una dirección IP")
    ip_parser.add_argument("target", help="IP objetivo (ej: 1.1.1.1)")
    ip_parser.add_argument("--geo",    action="store_true", help="Geolocalización")
    ip_parser.add_argument("--shodan", action="store_true", help="Búsqueda en Shodan (requiere API key)")
    ip_parser.add_argument("--all",    action="store_true", help="Ejecutar todos los análisis")
    ip_parser.add_argument("--report", action="store_true", help="Generar informe HTML")

    # --- Módulo: email ---
    email_parser = subparsers.add_parser("email", help="Analiza un email")
    email_parser.add_argument("target", help="Email objetivo (ej: usuario@ejemplo.com)")
    email_parser.add_argument("--validate", action="store_true", help="Validar formato y MX")
    email_parser.add_argument("--hibp",     action="store_true", help="Comprobar Have I Been Pwned")
    email_parser.add_argument("--all",      action="store_true", help="Ejecutar todos los análisis")
    email_parser.add_argument("--report",   action="store_true", help="Generar informe HTML")

    # --- Módulo: username ---
    user_parser = subparsers.add_parser("username", help="Busca un usuario en redes sociales")
    user_parser.add_argument("target", help="Nombre de usuario (ej: johndoe)")
    user_parser.add_argument("--report", action="store_true", help="Generar informe HTML")

    # --- Módulo: virustotal ---
    vt_parser = subparsers.add_parser("vt", help="Analiza un objetivo con VirusTotal")
    vt_parser.add_argument("target", help="URL, dominio, IP o hash (autodetectado)")
    vt_parser.add_argument("--type", choices=["url", "domain", "ip", "hash"],
                           help="Forzar tipo (si la autodetección falla)")
    vt_parser.add_argument("--report", action="store_true", help="Generar informe HTML")

    # --- Módulo: dorks ---
    dorks_parser = subparsers.add_parser("dorks", help="Genera Google Dorks para un objetivo")
    dorks_parser.add_argument("target", help="Dominio objetivo (ej: ejemplo.com)")
    dorks_parser.add_argument("--categories", nargs="+", metavar="CAT",
                              help="Filtrar por categorías (ej: --categories archivos credenciales)")
    dorks_parser.add_argument("--engine",   choices=["google", "bing"], default="google",
                              help="Motor de búsqueda (default: google)")
    dorks_parser.add_argument("--open",     action="store_true",
                              help="Abrir todas las búsquedas en el navegador")
    dorks_parser.add_argument("--list",     action="store_true",
                              help="Solo listar queries sin URLs completas")
    dorks_parser.add_argument("--custom",   metavar="QUERY",
                              help='Dork personalizado (usa {target} como placeholder)')
    dorks_parser.add_argument("--list-categories", action="store_true",
                              help="Mostrar categorías disponibles")
    dorks_parser.add_argument("--report",   action="store_true", help="Generar informe HTML")

    args = parser.parse_args()

    if not args.module:
        parser.print_help()
        sys.exit(0)

    # --- Enrutamiento a módulos ---
    if args.module == "domain":
        from modules.domain import DomainAnalyzer
        analyzer = DomainAnalyzer(args.target)
        results = analyzer.run(
            whois=args.whois or args.all,
            dns=args.dns or args.all,
            subdomains=args.subdomains or args.all,
        )
        if args.report:
            from reporters.html_reporter import generate_report
            generate_report("domain", args.target, results)

    elif args.module == "ip":
        from modules.ip import IPAnalyzer
        analyzer = IPAnalyzer(args.target)
        results = analyzer.run(
            geo=args.geo or args.all,
            shodan=args.shodan or args.all,
        )
        if args.report:
            from reporters.html_reporter import generate_report
            generate_report("ip", args.target, results)

    elif args.module == "email":
        from modules.email_check import EmailAnalyzer
        analyzer = EmailAnalyzer(args.target)
        results = analyzer.run(
            validate=args.validate or args.all,
            hibp=args.hibp or args.all,
        )
        if args.report:
            from reporters.html_reporter import generate_report
            generate_report("email", args.target, results)

    elif args.module == "username":
        from modules.username import UsernameAnalyzer
        analyzer = UsernameAnalyzer(args.target)
        results = analyzer.run()
        if args.report:
            from reporters.html_reporter import generate_report
            generate_report("username", args.target, results)

    elif args.module == "vt":
        from modules.virustotal import VirusTotalAnalyzer
        analyzer = VirusTotalAnalyzer(args.target)
        results  = analyzer.run(force_type=args.type)
        if args.report:
            from reporters.html_reporter import generate_report
            generate_report("vt", args.target, results)

    elif args.module == "dorks":
        from modules.dorks import DorksAnalyzer, list_categories

        if args.list_categories:
            list_categories()
            sys.exit(0)

        analyzer = DorksAnalyzer(args.target)

        if args.custom:
            results = analyzer.run_custom(args.custom, engine=args.engine)
        else:
            results = analyzer.run(
                categories=args.categories,
                engine=args.engine,
                open_browser=args.open,
                list_only=args.list,
            )

        if args.report:
            from reporters.html_reporter import generate_report
            generate_report("dorks", args.target, results)


if __name__ == "__main__":
    main()
