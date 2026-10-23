"""Print Shivalik instructions and validate a local layout."""

from pathlib import Path

URL = "https://github.com/moonis-ali/Dataset"


def validate(root: str | Path) -> list[str]:
    """Return missing expected directories without downloading anything."""
    location = Path(root)
    return [name for name in ("las", "classifications") if not (location / name).is_dir()]


def main() -> None:
    """Print manual Shivalik dataset instructions."""
    print(f"Official information: {URL}")
    print("Download LAS and classification files manually into las/ and classifications/.")
    print("Field-table column names must be confirmed from the released documentation.")
    print("No files are downloaded by this script.")


if __name__ == "__main__":
    main()
