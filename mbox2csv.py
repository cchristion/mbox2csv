"""Python Script to parse Mbox to csv."""
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "beautifulsoup4~=4.12.2",
#     "pandas~=2.2.3",
# ]
# ///

import argparse
import mailbox
import warnings
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)


def cli() -> dict:
    """CLI for Mbox to CSV parser."""
    parser = argparse.ArgumentParser(
        description="Mbox to CSV parser.",
    )
    parser.add_argument(
        "mbox_file",
        type=Path,
        help="Path to Mbox file",
    )
    parser.add_argument(
        "-o",
        "--output_csv",
        type=Path,
        help="Path to Output CSV",
    )
    args = parser.parse_args()
    return vars(args)


def mbox2csv(mbox_file: Path, output_file: Path) -> None:
    """Convert mbox file to csv."""
    mbox = mailbox.mbox(mbox_file)
    all_data = []
    for _, msg in mbox.iteritems():
        data = {}
        for key in msg.keys():
            data[key] = msg.get(key)
        try:
            body = ""
            body_part = msg.get_payload(decode=True)
            if body_part:
                body += body_part.decode(
                    msg.get_charset() or "ISO-8859-1",
                    errors="ignore",
                )
        except Exception as err:
            print(err)

        if body:
            soup = BeautifulSoup(body, "html.parser")
            body = soup.get_text(separator="\n", strip=True)
            data["body"] = body

        for part in msg.walk():
            filename = part.get_filename()
            if filename:
                data["filename"] = filename

        all_data.append(data)

    if output_file:
        mbox_df = pd.DataFrame(all_data)
        print(f"Extracted {len(mbox_df.columns)} fields from {mbox_file}")

        print(f"Writing to: {output_file}")
        mbox_df.to_csv(output_file, escapechar="\\", index=False)

        print("Sample Data:")
        print(mbox_df.sample(5))


if __name__ == "__main__":
    args = cli()
    mbox2csv(args["mbox_file"], args["output_csv"])
