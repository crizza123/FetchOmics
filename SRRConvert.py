#!/usr/bin/env python3
import os
import csv
import logging
import argparse
import subprocess

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def process_srr_file(csv_file, output_dir):
    """Process the given SRR CSV file."""
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            srr_id = row[0]
            logging.info(f"Processing {srr_id} from {csv_file}")
            try:
                result = subprocess.run(
                    ['fasterq-dump', srr_id, '-O', output_dir],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                logging.info(result.stdout)
            except subprocess.CalledProcessError as e:
                logging.error(f"Error processing {srr_id}: {e.stderr}")

def process_gse(gse_id, base_dir):
    """Process a given GSE id by locating its SRR CSV file in the GSE-specific directory."""
    csv_file = os.path.join(base_dir, gse_id, f"{gse_id}_SRR.csv")
    if not os.path.exists(csv_file):
        logging.warning(f"Skipping {gse_id}, missing {csv_file}")
        return

    logging.info(f"Found {csv_file}. Beginning processing.")
    output_dir = os.path.join(base_dir, gse_id)  # Set output directory to GSE_ID directory
    process_srr_file(csv_file, output_dir)

def main():
    setup_logging()

    parser = argparse.ArgumentParser(
        description="SRR Conversion Script: Processes SRR CSV files located in GSE-specific subdirectories."
    )
    parser.add_argument(
        '--base_dir',
        type=str,
        required=True,
        help="Base directory where the GSE directories are located."
    )
    parser.add_argument(
        '--gse_list',
        nargs='+',
        required=True,
        help="List of GSE ids to process (e.g., GSE113046 GSE106973 ...)"
    )

    args = parser.parse_args()

    for gse_id in args.gse_list:
        process_gse(gse_id, args.base_dir)

if __name__ == '__main__':
    main()
