"""Check dataset web links without downloading dataset files."""

from pathlib import Path
import re
from urllib.request import Request, urlopen


README = Path(__file__).parents[1] / "README.md"
URL_PATTERN = re.compile(r"https?://[^\s|)]+")


def read_links() -> list[str]:
    """Return unique HTTP links written in the dataset table."""
    return list(dict.fromkeys(URL_PATTERN.findall(README.read_text())))


def check(url: str) -> str:
    """Return a short status for one URL using a HEAD request."""
    try:
        request = Request(url, method="HEAD", headers={"User-Agent": "canopy-mapping-rover-link-checker/1.0"})
        with urlopen(request, timeout=15) as response:
            return f"OK ({response.status})"
    except Exception as error:
        return f"BROKEN ({type(error).__name__}: {error})"


def main() -> None:
    """Print one result per link."""
    for link in read_links():
        print(f"{check(link)} {link}")


if __name__ == "__main__":
    main()
