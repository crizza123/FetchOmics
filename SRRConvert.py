#!/usr/bin/env python3

import os
import sys
import csv
import argparse
import subprocess

def log_message(msg, level="INFO"):
    print(f"[{level}] {msg}")

# Checks if .sra file already exists in the correct nested directory
def file_exists(srr, base_dir, gse_id):
    srr_path = os.path.join(base_dir, gse_id, srr, srr, f"{srr}.sra")
    return os.path.isfile(srr_path)

def download_sra_files(run_ids, base_dir, gse_id, max_size):
    gse_dir = os.path.join(base_dir, gse_id)
    log_message(f"Ensuring GSE directory exists: {gse_dir}", "DEBUG")
    os.makedirs(gse_dir, exist_ok=True)

    for run_id in run_ids:
        srr_parent_dir = os.path.join(gse_dir, run_id)
        srr_dir = os.path.join(srr_parent_dir, run_id)
        sra_path = os.path.join(srr_dir, f"{run_id}.sra")

        if file_exists(run_id, base_dir, gse_id):
            log_message(f".sra file for {run_id} already exists. Skipping download.", "INFO")
            continue

        os.makedirs(srr_dir, exist_ok=True)
        prefetch_cmd = ["prefetch", run_id, "-O", srr_dir, "--max-size", max_size]
        log_message(f"Running cmd: {' '.join(prefetch_cmd)}", "DEBUG")

        try:
            subprocess.run(prefetch_cmd, check=True, text=True)
            log_message(f"Successfully downloaded {run_id}")
        except subprocess.CalledProcessError as e:
            log_message(f"Error downloading {run_id}: {e}", level="ERROR")

        if not os.path.isfile(sra_path):
            log_message(f"{sra_path} not found after prefetch.", level="WARNING")

def convert_sra_to_fastq(run_ids, base_dir, gse_id, paired=False):
    for run_id in run_ids:
        srr_dir = os.path.join(base_dir, gse_id, run_id, run_id)
        sra_path = os.path.join(srr_dir, f"{run_id}.sra")

        if not os.path.exists(sra_path):
            log_message(f"{sra_path} does not exist. Skipping conversion.", "WARNING")
            continue

        log_message(f"Converting {run_id}.sra to FASTQ", "DEBUG")
        conv_cmd = [
            "fasterq-dump",
            "--split-files",
            "--threads", "4",
            sra_path,
            "-O", srr_dir
        ]

        try:
            subprocess.run(conv_cmd, check=True, text=True)
        except subprocess.CalledProcessError as e:
            log_message(f"fasterq-dump failed for {run_id}: {e}", level="ERROR")
            continue

        if not paired:
            single_fastq = os.path.join(srr_dir, f"{run_id}_1.fastq")
            target_fastq = os.path.join(srr_dir, f"{run_id}.fastq")
            if os.path.exists(single_fastq):
                os.rename(single_fastq, target_fastq)
                log_message(f"Renamed '{run_id}_1.fastq' to '{run_id}.fastq'")

def read_run_ids_from_csv(base_dir, gse_id):
    csv_path = os.path.join(base_dir, gse_id, f"{gse_id}_SRR.csv")

    if not os.path.isfile(csv_path):
        log_message(f"CSV file not found: {csv_path}", level="ERROR")
        return None

    run_ids = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            next(f, None)  # Skip header
            for line in f:
                line = line.strip()
                if line:
                    run_ids.append(line)
    except Exception as e:
        log_message(f"Error reading {csv_path}: {e}", level="ERROR")
        return None

    return run_ids

def main():
    parser = argparse.ArgumentParser(
        description="Downloads .sra files if not present, converts to FASTQ."
    )
    parser.add_argument("--base_dir", required=True, help="Base directory for GSE folders")
    parser.add_argument("--gse_list", nargs="+", required=True, help="List of GSE IDs")
    parser.add_argument("--paired", action="store_true", help="Treat runs as paired-end")
    parser.add_argument("--skip_download", action="store_true", help="Skip prefetch step")
    parser.add_argument("--max_size", default="100GB", help="Max size for prefetch")
    args = parser.parse_args()

    for gse_id in args.gse_list:
        log_message(f"Processing GSE: {gse_id}", "INFO")

        run_ids = read_run_ids_from_csv(args.base_dir, gse_id)
        if not run_ids:
            log_message(f"No run IDs for {gse_id}. Skipping.", "ERROR")
            continue

        if not args.skip_download:
            download_sra_files(run_ids, args.base_dir, gse_id, args.max_size)
        else:
            log_message(f"Skipping download for {gse_id} as per user request.", "INFO")

        convert_sra_to_fastq(run_ids, args.base_dir, gse_id, paired=args.paired)
        log_message(f"Finished processing {gse_id}\n", "INFO")

if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        log_message(f"Unhandled exception: {ex}", "ERROR")
        sys.exit(2)