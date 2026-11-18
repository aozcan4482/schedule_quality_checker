"""Select Excel workbooks for a schedule quality audit."""

import argparse
from pathlib import Path


def select_workbooks(path: Path) -> list[Path]:
    if path.is_file():
        if path.suffix.lower() != ".xlsx" or path.name.startswith("~$"):
            raise ValueError(f"Expected an Excel .xlsx workbook: {path}")
        return [path]

    if not path.is_dir():
        raise ValueError(f"Input path does not exist: {path}")

    workbooks = sorted(
        entry
        for entry in path.iterdir()
        if entry.is_file()
        and entry.suffix.lower() == ".xlsx"
        and not entry.name.startswith("~$")
    )
    if not workbooks:
        raise ValueError(f"No .xlsx workbooks found in: {path}")
    return workbooks


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List the Excel workbooks selected for a schedule quality audit."
    )
    parser.add_argument(
        "path", type=Path, help="An .xlsx workbook or a folder of workbooks"
    )
    args = parser.parse_args()
    try:
        workbooks = select_workbooks(args.path)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    for workbook in workbooks:
        print(workbook)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
