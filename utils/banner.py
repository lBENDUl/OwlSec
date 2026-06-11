"""
utils/banner.py — Banner ASCII y colores para la CLI
"""

import random

# ── Códigos ANSI ─────────────────────────────────────────────────────────────
class Colors:
    CYAN    = "\033[96m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    RED     = "\033[91m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RESET   = "\033[0m"

    @staticmethod
    def ok(text):      return f"{Colors.GREEN}[+]{Colors.RESET} {text}"
    @staticmethod
    def info(text):    return f"{Colors.CYAN}[*]{Colors.RESET} {text}"
    @staticmethod
    def warn(text):    return f"{Colors.YELLOW}[!]{Colors.RESET} {text}"
    @staticmethod
    def error(text):   return f"{Colors.RED}[-]{Colors.RESET} {text}"
    @staticmethod
    def section(text): return f"\n{Colors.BOLD}{Colors.BLUE}{'─'*50}\n  {text}\n{'─'*50}{Colors.RESET}"


# ── Banner: búho ASCII ────────────────────────────────────────────────────────
_OWL = r"""
    /\___/\
   (  o o  )
   (  =^=  )
  /|       |\
 (_|_______|_)
   |  | |  |
   (_/ (_/
"""

_BANNER_OWL = (
    f"{Colors.CYAN}{Colors.BOLD}{_OWL}{Colors.RESET}"
    f"{Colors.BOLD}  OwlSec{Colors.RESET}  {Colors.DIM}— OSINT Toolkit v0.1{Colors.RESET}\n"
    f"{Colors.DIM}  Passive Recon · github.com/tu-usuario/owlsec{Colors.RESET}\n"
)

# ── Banner: nombre en ASCII art ───────────────────────────────────────────────
_BANNER_NAME = (
    f"{Colors.CYAN}{Colors.BOLD}\n"
    f"   ██████╗ ██╗    ██╗██╗     ███████╗███████╗ ██████╗\n"
    f"  ██╔═══██╗██║    ██║██║     ██╔════╝██╔════╝██╔════╝\n"
    f"  ██║   ██║██║ █╗ ██║██║     ███████╗█████╗  ██║     \n"
    f"  ██║   ██║██║███╗██║██║     ╚════██║██╔══╝  ██║     \n"
    f"  ╚██████╔╝╚███╔███╔╝███████╗███████║███████╗╚██████╗\n"
    f"   ╚═════╝  ╚══╝╚══╝ ╚══════╝╚══════╝╚══════╝ ╚═════╝\n"
    f"{Colors.RESET}"
    f"{Colors.DIM}  OSINT Toolkit v0.1 — Passive Recon{Colors.RESET}\n"
    f"{Colors.DIM}  github.com/tu-usuario/owlsec{Colors.RESET}\n"
)

# ── Alterna aleatoriamente entre los dos banners ──────────────────────────────
def print_banner():
    print(random.choice([_BANNER_OWL, _BANNER_NAME]))
