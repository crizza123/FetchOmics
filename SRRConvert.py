#!/usr/bin/env python3
"""
SRRConvert.py

This script processes SRR CSV files for each specified GSE id. It reads the CSV file,
which is expected to be located in a subdirectory under the base directory (i.e.,
<base_dir>/<GSE_ID>/<GSE_ID>_SRR.csv). For each SRR id in the CSV, the script runs an external
conversion command (e.g., fasterq-dump).

Usage:
    python SRRConvert.py --base_dir /path/to/base --gse_list GSE113046 GSE106973 ...
"""

import os
import csv
import logging
import argparse
import subprocess
from typing import List

def setup_logging() -> None:
    """
    Configure the logging format and level.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        An argparse.Namespace object with the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Process SRR CSV files located in GSE-specific subdirectories."
    )
    parser.add_argument(
        "--base_dir",
        required=True,
        help="Base directory containing GSE subdirectories (e.g., /nfs/turbo/umms-sihogan/crizza/FetchOmics)."
    )
    parser.add_argument(
        "--gse_list",
        required=True,
        nargs="+",
        help="List of GSE IDs to process (e.g., GSE113046 GSE106973)."
    )
    return parser.parse_args()

def process_srr_file(csv_file: str, output_dir: str) -> None:
    """
    Process a single SRR CSV file by reading each SRR id and running a conversion command.

    Args:
        csv_file (str): Full path to the SRR CSV file.
        output_dir (str): Directory where the converted files will be saved.
    """
    try:
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                # Skip empty rows.
                if not row:
                    continue

                srr_id = row[0].strip()  # Assuming the first column contains the SRR id.
                logging.info(f"Processing SRR id '{srr_id}' from file: {csv_file}")

                try:
                    # Run the conversion command (adjust the command as needed)
                    result = subprocess.run(
                        ['fasterq-dump', srr_id, '-O', output_dir],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    logging.info(f"Conversion output for {srr_id}:\n{result.stdout}")
                except subprocess.CalledProcessError as e:
                    logging.error(f"Error processing {srr_id}:\n{e.stderr}")
    except Exception as e:
        logging.error(f"Failed to process file '{csv_file}': {str(e)}")

def process_gse(gse_id: str, base_dir: str, output_dir: str) -> None:
    """
    Process a single GSE id by locating its corresponding SRR CSV file and processing it.

    Args:
        gse_id (str): GEO series id (e.g., 'GSE113046').
        base_dir (str): Base directory containing GSE-specific subdirectories.
        output_dir (str): Directory where output files will be saved.
    """
    # Construct the expected CSV file path:
    csv_file = os.path.join(base_dir, gse_id, f"{gse_id}_SRR.csv")
    if not os.path.exists(csv_file):
        logging.warning(f"Skipping {gse_id}: missing file {csv_file}")
        return

    logging.info(f"Found CSV file for {gse_id}: {csv_file}. Beginning processing.")
    process_srr_file(csv_file, output_dir)

def main() -> None:
    """
    Main function: parses arguments, then processes each provided GSE id.
    """
    setup_logging()
    args = parse_arguments()

    # Define an output directory for converted files.
    # You can modify this as needed or add an additional argument.
    output_dir = "./output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        logging.info(f"Created output directory: {output_dir}")

    # Process each GSE id in the provided list.
    for gse in args.gse_list:
        logging.info(f"Starting processing for {gse}")
        process_gse(gse, args.base_dir, output_dir)

if __name__ == '__main__':
    main()
