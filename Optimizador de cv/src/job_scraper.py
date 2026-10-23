import re
import requests
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urlparse

class JobScraperError(Exception):
    """Excepción para errores de scraping con indicación si requiere pegado manual."""
    def __init__(self, message: str, requires_manual: bool = False):
        super().__init__(message)
        self.requires_manual = requires_manual

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# Dominios que comúnmente requieren inicio de sesión o tienen muros antibot
PROTECTED_DOMAINS = ["linkedin.com", "indeed.com", "glassdoor.com", "computrabajo.com"]

def extract_job_content(url: str) -> str:
    """
    Extrae el texto relevante de la oferta de trabajo desde una URL.
    Lanza JobScraperError si la página está bloqueada o requiere autenticación.
    """
    clean_url = url.strip()
    if not clean_url:
        raise JobScraperError("La URL de la vacante está vacía.", requires_manual=False)

    if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
        clean_url = "https://" + clean_url

    parsed = urlparse(clean_url)
    domain = parsed.netloc.lower()

    # Detección temprana de portales fuertemente protegidos
    for protected in PROTECTED_DOMAINS:
        if protected in domain:
            # Intentaremos el fetch, pero si falla sabemos con certeza que requiere fallback
            pass

    try:
        response = requests.get(clean_url, headers=BROWSER_HEADERS, timeout=12)
    except requests.exceptions.Timeout:
        raise JobScraperError(
            "El servidor de la vacante tardó demasiado en responder (Timeout).",
            requires_manual=True
        )
    except requests.exceptions.RequestException as e:
        raise JobScraperError(
            f"No se pudo conectar a la URL: {str(e)[:100]}",
            requires_manual=True
        )

    # Detección de bloqueos HTTP comunes
    if response.status_code in [401, 403, 429, 999]:
        raise JobScraperError(
            f"El portal de empleo bloqueó el acceso automatizado (Código HTTP {response.status_code}). "
            "Por favor pega la descripción de la vacante manualmente.",
            requires_manual=True
        )

    if response.status_code != 200:
        raise JobScraperError(
            f"La página respondió con error {response.status_code}.",
            requires_manual=True
        )

    html_text = response.text

    # Detección de muros de login / authwall en el contenido
    if "authwall" in html_text.lower() or "login-submit" in html_text.lower() or "cloudflare" in html_text.lower() and "verify" in html_text.lower():
        raise JobScraperError(
            "El portal de empleo requiere iniciar sesión para ver la vacante. "
            "Copia y pega la descripción en el cuadro inferior.",
            requires_manual=True
        )

    # 1. Extracción con Trafilatura (óptimo para contenido estructurado)
    extracted = trafilatura.extract(
        html_text, 
        include_comments=False, 
        include_tables=True,
        no_fallback=False
    )

    # 2. Fallback con BeautifulSoup si Trafilatura no extrajo suficiente texto
    if not extracted or len(extracted.strip()) < 100:
        soup = BeautifulSoup(html_text, "html.parser")
        
        # Eliminar scripts y estilos
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()

        # Buscar contenedores típicos de ofertas de trabajo
        candidates = soup.find_all(
            ["div", "article", "section", "main"], 
            class_=re.compile(r"(job|description|detail|posting|vacancy|offer)", re.I)
        )
        
        if candidates:
            extracted = "\n".join([c.get_text(separator="\n", strip=True) for c in candidates])
        else:
            extracted = soup.get_text(separator="\n", strip=True)

    final_text = extracted.strip() if extracted else ""
    # Filtrar exceso de saltos de línea repetidos
    final_text = re.sub(r"\n{3,}", "\n\n", final_text)

    if len(final_text) < 80:
        raise JobScraperError(
            "No se pudo extraer suficiente texto relevante de la página de la vacante. "
            "Por favor pega los requisitos y responsabilidades manualmente.",
            requires_manual=True
        )

    return final_text
