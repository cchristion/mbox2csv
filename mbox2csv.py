"""Python Script to parse Mbox to csv."""
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "beautifulsoup4~=4.12.2",
#     "pandas~=2.2.3",
# ]
# ///

import argparse
import logging
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
        "--output_dir",
        type=Path,
        help='Path to Output Directory. default "mbox_output"',
        default="mbox_output",
    )
    args = parser.parse_args()
    return vars(args)


def mbox2csv(mbox_file: Path, output_dir: Path) -> None:
    """Convert mbox file to csv."""
    mbox = mailbox.mbox(mbox_file)
    all_data = []
    extracted_files = 0
    Path(args["output_dir"]).mkdir(parents=True, exist_ok=True)
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
        except Exception:
            logging.exception("Message Error")

        if body:
            soup = BeautifulSoup(body, "html.parser")
            body = soup.get_text(separator="\n", strip=True)
            data["body"] = body

        for part in msg.walk():
            filename = part.get_filename()
            if filename:
                data["filename"] = filename
                if output_dir:
                    try:
                        with Path.open(
                            output_dir / filename.replace("/", "_"),
                            "wb",
                        ) as f:
                            f.write(part.get_payload(decode=True))
                        logging.info("Saved attachment %s", filename)
                        extracted_files += 1
                    except Exception:
                        logging.exception("Unable to Save attachment %s", filename)

        all_data.append(data)

    logging.info("Extracted %d files", extracted_files)
    if output_dir:
        mbox_df = pd.DataFrame(all_data)
        logging.info("Extracted %d fields from %s", len(mbox_df.columns), mbox_file)

        logging.info("Writing CSV to %s", output_dir / "final.csv")
        mbox_df.to_csv(output_dir / "final.csv", escapechar="\\", index=False)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s : %(levelname)s : %(message)s",
        datefmt="%Y%m%dT%H%M%S",
        encoding="utf-8",
        level=logging.INFO,
    )

    args = cli()
    logging.info("Parsing %s", args["mbox_file"])
    logging.info("Writing Output to %s", args["output_dir"])
    mbox2csv(args["mbox_file"], args["output_dir"])
