"""Print TreeScope instructions and validate a local, user-provided layout."""

from pathlib import Path

URL = "https://treescope.org/data_overview/"
EXPECTED = ("bags", "labels")


def validate(root: str | Path) -> list[str]:
    """Return missing expected directories without downloading anything."""
    location = Path(root)
    return [name for name in EXPECTED if not (location / name).is_dir()]


def main() -> None:
    """Print manual instructions for a small TreeScope sequence."""
    print(f"Official information: {URL}")
    print("Download one sequence manually, then place bags/ and labels/ under the chosen root.")
    print("No files are downloaded by this script.")


if __name__ == "__main__":
    main()
