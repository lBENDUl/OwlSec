# 🦉 OwlSec — OSINT Toolkit

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Actualizandose-blue)

---

## ✨ Módulos

| Módulo       | Descripción                                               |
|--------------|-----------------------------------------------------------|
| `domain`     | WHOIS, enumeración DNS, subdominios vía crt.sh            |
| `ip`         | Geolocalización, integración Shodan                       |
| `email`      | Validación + registros MX, Have I Been Pwned              |
| `username`   | Búsqueda en 15+ plataformas sociales en paralelo          |
| `vt`         | Análisis con VirusTotal (URL, dominio, IP, hash)          |
| `dorks`      | Generador de Google Dorks con 35+ queries categorizados   |

Todos los módulos generan un **informe HTML** con sidebar de navegación, secciones colapsables y diseño dark profesional.

---

## 🚀 Instalación

```bash
git clone https://github.com/lBENDUl/owlsec.git
cd owlsec
pip install -r requirements.txt
```

Configura tus API keys en `config.yaml`:
```yaml
shodan_api_key:      "KEY"
hibp_api_key:        "KEY"
virustotal_api_key:  "KEY"
```

---

## 📖 Uso

```bash
# Dominio — análisis completo con informe
python owlsec.py domain ejemplo.com --all --report

# IP con geolocalización y Shodan
python owlsec.py ip 1.1.1.1 --all --report

# Email — validar y comprobar brechas
python owlsec.py email usuario@ejemplo.com --all --report

# Username en redes sociales
python owlsec.py username johndoe --report

# VirusTotal — autodetecta el tipo
python owlsec.py vt ejemplo.com --report
python owlsec.py vt 1.1.1.1 --report
python owlsec.py vt https://sitio-sospechoso.com --report
python owlsec.py vt d41d8cd98f00b204e9800998ecf8427e --report

# Google Dorks
python owlsec.py dorks ejemplo.com --report
python owlsec.py dorks ejemplo.com --categories credenciales directorios
python owlsec.py dorks ejemplo.com --open
python owlsec.py dorks ejemplo.com --custom 'site:{target} ext:sql'
```

---

## 📁 Estructura

```
owlsec/
├── owlsec.py             # CLI principal
├── config.yaml           # API keys (no subir a Git)
├── modules/
│   ├── domain.py         # WHOIS, DNS, subdominios
│   ├── ip.py             # Geolocalización, Shodan
│   ├── email_check.py    # Validación, HIBP
│   ├── username.py       # Búsqueda en redes sociales
│   ├── virustotal.py     # VirusTotal API v3
│   └── dorks.py          # Google Dorks generator
├── reporters/
│   └── html_reporter.py  # Informes HTML profesionales
├── utils/
│   ├── banner.py         # ASCII art (búho / nombre)
│   ├── logger.py         # Logger con colores ANSI
│   └── config.py         # Carga de config.yaml
└── output/               # Informes generados
```

---

## ⚠️ Aviso legal

OwlSec es para uso **ético y legal** únicamente.  
Úsala exclusivamente sobre sistemas para los que tengas autorización explícita.  
El autor no se responsabiliza del uso indebido.

---

## 📄 Licencia

MIT License — ver [LICENSE](LICENSE)
