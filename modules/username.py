"""
modules/username.py — Búsqueda de username en redes sociales
"""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.banner import Colors
from utils.logger import get_logger

logger = get_logger()

# Plataformas a comprobar: {nombre: url con {username}}
PLATFORMS = {
    "GitHub":        "https://github.com/{username}",
    "Twitter/X":     "https://x.com/{username}",
    "Instagram":     "https://www.instagram.com/{username}/",
    "Reddit":        "https://www.reddit.com/user/{username}",
    "LinkedIn":      "https://www.linkedin.com/in/{username}",
    "TikTok":        "https://www.tiktok.com/@{username}",
    "YouTube":       "https://www.youtube.com/@{username}",
    "Twitch":        "https://www.twitch.tv/{username}",
    "Pinterest":     "https://www.pinterest.com/{username}",
    "HackerNews":    "https://news.ycombinator.com/user?id={username}",
    "Dev.to":        "https://dev.to/{username}",
    "Keybase":       "https://keybase.io/{username}",
    "GitLab":        "https://gitlab.com/{username}",
    "Pastebin":      "https://pastebin.com/u/{username}",
    "Medium":        "https://medium.com/@{username}",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; osint-toolkit/0.1)"}


class UsernameAnalyzer:

    def __init__(self, target: str):
        self.target = target.strip()
        self.results = {}

    def run(self) -> dict:
        print(Colors.section(f"USERNAME: {self.target}"))
        print(Colors.info(f"Comprobando {len(PLATFORMS)} plataformas...\n"))

        found = []
        not_found = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(self._check, platform, url): platform
                for platform, url in PLATFORMS.items()
            }
            for future in as_completed(futures):
                platform = futures[future]
                exists, url = future.result()
                if exists:
                    found.append({"platform": platform, "url": url})
                    print(Colors.ok(f"{platform:15} → {url}"))
                else:
                    not_found.append(platform)

        print(f"\n{Colors.GREEN}{Colors.BOLD}Encontrado en {len(found)} plataformas.{Colors.RESET}")

        self.results = {
            "username": self.target,
            "found": found,
            "not_found": not_found,
            "total_checked": len(PLATFORMS),
        }
        return self.results

    def _check(self, platform: str, url_template: str):
        url = url_template.format(username=self.target)
        try:
            r = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
            # Heurística básica: 200 sin redirección sospechosa = existe
            exists = r.status_code == 200 and self.target.lower() in r.url.lower()
            return exists, url
        except Exception:
            return False, url
