"""Check dataset web links without downloading dataset files."""

from pathlib import Path
import re
from urllib.request import Request, urlopen


README = Path(__file__).parents[1] / "README.md"
URL_PATTERN = re.compile(r"https?://[^\s|)]+")
TRAILING_PUNCTUATION = ".,;:'\""


def read_links() -> list[str]:
    """Return unique HTTP links written in the dataset table."""
    links = (link.rstrip(TRAILING_PUNCTUATION) for link in URL_PATTERN.findall(README.read_text()))
    return list(dict.fromkeys(links))


def check(url: str) -> str:
    """Return a short status, retrying with GET when HEAD is rejected."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; canopy-mapping-rover-link-checker/1.0)"}
    for method in ("HEAD", "GET"):
        for _attempt in range(3):
            try:
                request = Request(url, method=method, headers=headers)
                with urlopen(request, timeout=15) as response:
                    if method == "GET":
                        response.read(1)
                    suffix = ", GET fallback" if method == "GET" else ""
                    return f"OK ({response.status}{suffix})"
            except Exception as error:
                last_error = error
    return f"BROKEN ({type(last_error).__name__}: {last_error})"


def main() -> None:
    """Print one result per link."""
    for link in read_links():
        print(f"{check(link)} {link}")


if __name__ == "__main__":
    main()
