"""Print DigiForests instructions and validate a local layout."""

from pathlib import Path

URL = "https://www.ipb.uni-bonn.de/data/digiforest-dataset/"


def validate(root: str | Path) -> list[str]:
    """Return missing expected directories without downloading anything."""
    location = Path(root)
    return [name for name in ("pointclouds", "labels") if not (location / name).is_dir()]


def main() -> None:
    """Print manual DigiForests instructions."""
    print(f"Official information: {URL}")
    print("Download files manually and place pointclouds/ and labels/ under the chosen root.")
    print("No files are downloaded by this script.")


if __name__ == "__main__":
    main()
