#!/usr/bin/env python3

import os
import sys
import csv
import argparse
import subprocess

def log_message(msg, level="INFO"):
    """Utility function to log a message with a specified level."""
    print(f"[{level}] {msg}")

def download_sra_files(run_ids, base_dir, gse_id):
    """
    Downloads .sra files for each run in `run_ids`, placing them into:
        <base_dir>/<GSE_ID>/<SRR_ID>/<SRR_ID>/<SRR_ID>.sra

    We create two subdirectories both named SRR_ID, e.g.:
        srr_parent_dir = <base_dir>/<GSE_ID>/<SRR_ID>
        srr_dir        = <base_dir>/<GSE_ID>/<SRR_ID>/<SRR_ID>
    """
    gse_dir = os.path.join(base_dir, gse_id)
    log_message(f"[download_sra_files] Ensuring GSE directory exists: {gse_dir}", "DEBUG")
    os.makedirs(gse_dir, exist_ok=True)

    for run_id in run_ids:
        # First-level SRR directory
        srr_parent_dir = os.path.join(gse_dir, run_id)
        log_message(f"[download_sra_files] Creating/using SRR parent directory: {srr_parent_dir}", "DEBUG")
        os.makedirs(srr_parent_dir, exist_ok=True)

        # Nested SRR directory
        srr_dir = os.path.join(srr_parent_dir, run_id)
        log_message(f"[download_sra_files] Creating/using nested SRR directory: {srr_dir}", "DEBUG")
        os.makedirs(srr_dir, exist_ok=True)

        # Where we expect to place the .sra
        sra_filename = f"{run_id}.sra"
        sra_path = os.path.join(srr_dir, sra_filename)
        log_message(f"[download_sra_files] Expecting to place {sra_filename} at: {sra_path}", "DEBUG")

        # Run prefetch
        prefetch_cmd = ["prefetch", run_id, "-O", srr_dir]
        log_message(f"[download_sra_files] Running cmd: {' '.join(prefetch_cmd)}", "DEBUG")

        try:
            subprocess.run(prefetch_cmd, check=True, text=True)
            log_message(f"Successfully downloaded {run_id} to {srr_dir}")
        except subprocess.CalledProcessError as e:
            log_message(f"Error downloading {run_id}: {e}", level="ERROR")
            continue

        # Verify presence
        if not os.path.isfile(sra_path):
            log_message(f"{sra_path} not found after prefetch.", level="WARNING")

def convert_sra_to_fastq(run_ids, base_dir, gse_id, paired=False):
    """
    Converts .sra files to FASTQ using fasterq-dump, looking for:
        <base_dir>/<GSE_ID>/<SRR_ID>/<SRR_ID>/<SRR_ID>.sra

    If 'paired=True', we treat them as paired-end, otherwise single-end.
    """
    gse_dir = os.path.join(base_dir, gse_id)
    log_message(f"[convert_sra_to_fastq] Checking GSE directory: {gse_dir}", "DEBUG")

    for run_id in run_ids:
        srr_parent_dir = os.path.join(gse_dir, run_id)
        srr_dir = os.path.join(srr_parent_dir, run_id)
        sra_path = os.path.join(srr_dir, f"{run_id}.sra")

        if not os.path.exists(sra_path):
            log_message(f"[convert_sra_to_fastq] {sra_path} does not exist. Skipping.", "WARNING")
            continue

        log_message(f"[convert_sra_to_fastq] Converting {run_id}.sra to FASTQ...", "DEBUG")
        conv_cmd = [
            "fasterq-dump",
            "--split-files",
            "--threads",
            "4",
            sra_path,
            "-O",
            srr_dir
        ]
        log_message(f"[convert_sra_to_fastq] Running cmd: {' '.join(conv_cmd)}", "DEBUG")

        try:
            subprocess.run(conv_cmd, check=True, text=True)
        except subprocess.CalledProcessError as e:
            log_message(f"fasterq-dump failed for {run_id}: {e}", level="ERROR")
            continue

        if paired:
            log_message(f"{run_id}: Paired-end data – FASTQ files split into _1 and _2.")
        else:
            # Single-end: rename *_1.fastq to <SRR_ID>.fastq
            single_fastq = os.path.join(srr_dir, f"{run_id}_1.fastq")
            target_fastq = os.path.join(srr_dir, f"{run_id}.fastq")
            if os.path.exists(single_fastq):
                log_message(f"[convert_sra_to_fastq] Renaming {single_fastq} -> {target_fastq}", "DEBUG")
                os.rename(single_fastq, target_fastq)
                log_message(f"{run_id}: Single-end data – renamed '{run_id}_1.fastq' to '{run_id}.fastq'.")

        # Optional: remove .sra to save space
        # log_message(f"[convert_sra_to_fastq] Removing {sra_path}", "DEBUG")
        # try:
        #     os.remove(sra_path)
        # except OSError:
        #     pass

def read_run_ids_from_csv(base_dir, gse_id):
    """
    Reads SRR IDs from:
        <base_dir>/<GSE_ID>/<GSE_ID>_SRR.csv

    Assumes first line is a header and subsequent lines each contain one SRR ID.
    Returns a list of SRR IDs.
    """
    csv_path = os.path.join(base_dir, gse_id, f"{gse_id}_SRR.csv")
    log_message(f"[read_run_ids_from_csv] Looking for {csv_path}", "DEBUG")

    if not os.path.isfile(csv_path):
        log_message(f"CSV file not found: {csv_path}", level="ERROR")
        return None

    run_ids = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            # Skip header line
            header = next(f, None)
            log_message(f"[read_run_ids_from_csv] Skipped header: {header}", "DEBUG")
            for line in f:
                line = line.strip()
                if line:
                    run_ids.append(line)
    except Exception as e:
        log_message(f"Error reading {csv_path}: {e}", level="ERROR")
        return None

    if not run_ids:
        log_message(f"No valid run IDs found in {csv_path}", level="ERROR")
        return None

    log_message(f"[read_run_ids_from_csv] Found {len(run_ids)} run IDs in {csv_path}", "DEBUG")
    return run_ids

def main():
    parser = argparse.ArgumentParser(
        description="SRRConvert: Downloads .sra files and converts them to FASTQ, "
                    "with a nested directory structure <base_dir>/<GSE_ID>/<SRR_ID>/<SRR_ID>/<SRR_ID>.sra"
    )
    parser.add_argument("--base_dir", required=True, help="Base directory (where GSE folders exist)")
    parser.add_argument("--gse_list", nargs="+", help="List of GSE IDs (e.g., GSE113046)")
    parser.add_argument("--paired", action="store_true", help="If set, treat all runs as paired-end.")
    args = parser.parse_args()

    log_message(f"Arguments: base_dir={args.base_dir}, gse_list={args.gse_list}, paired={args.paired}", "DEBUG")

    if not args.gse_list:
        log_message("No GSE ID(s) provided to --gse_list. Exiting.", level="ERROR")
        sys.exit(2)

    for gse_id in args.gse_list:
        if not gse_id:
            continue
        log_message(f"Processing GSE: {gse_id}", "INFO")

        # 1) Read run IDs
        run_ids = read_run_ids_from_csv(args.base_dir, gse_id)
        if not run_ids:
            log_message(f"Failed to read run IDs for {gse_id}. Skipping this GSE.", "ERROR")
            continue

        # 2) Download .sra
        log_message(f"Downloading SRA files for GSE: {gse_id}", "INFO")
        download_sra_files(run_ids, args.base_dir, gse_id)

        # 3) Convert to FASTQ
        log_message(f"Converting SRA to FASTQ for GSE: {gse_id}", "INFO")
        convert_sra_to_fastq(run_ids, args.base_dir, gse_id, paired=args.paired)

        log_message(f"Finished processing GSE: {gse_id}\n", "INFO")

if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        log_message(f"Unhandled exception: {ex}", "ERROR")
        sys.exit(2)
