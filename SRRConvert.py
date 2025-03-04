#!/usr/bin/env python3

import os
import sys
import argparse
import subprocess
import csv

def log_message(msg, level="INFO"):
    print(f"[{level}] {msg}")

def read_runinfo_csv(csv_path):
    """
    Reads a CSV (e.g. SRA RunInfo) and returns a dict: { run_id -> layout }, 
    where layout is 'SINGLE' or 'PAIRED'.
    """
    runinfo_dict = {}
    try:
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                run_id = row.get("Run", "").strip()
                layout = row.get("LibraryLayout", "SINGLE").strip().upper()
                if run_id:
                    runinfo_dict[run_id] = layout
    except FileNotFoundError:
        log_message(f"Could not find CSV: {csv_path}", level="ERROR")
    except Exception as e:
        log_message(f"Error reading CSV: {e}", level="ERROR")
    return runinfo_dict

def convert_sra_to_fastq(run_ids, base_dir, gse_id, runinfo_dict=None):
    """
    Converts .sra to FASTQ for each SRR ID in the older nested structure:
        base_dir/GSE_ID/SRR_ID/SRR_ID/SRR_ID.sra
    Checks runinfo_dict for 'SINGLE'/'PAIRED'; defaults to 'SINGLE' if missing.
    """
    gse_dir = os.path.join(base_dir, gse_id)
    
    for run_id in run_ids:
        # Nested path: <base_dir>/<GSE_ID>/<SRR_ID>/<SRR_ID>/<SRR_ID>.sra
        srr_parent_dir = os.path.join(gse_dir, run_id)
        srr_dir = os.path.join(srr_parent_dir, run_id)
        sra_path = os.path.join(srr_dir, f"{run_id}.sra")

        if not os.path.exists(sra_path):
            log_message(f"{sra_path} does not exist. Skipping.", level="WARNING")
            continue

        # Convert to FASTQ
        log_message(f"Converting {run_id}.sra to FASTQ...")
        conv_cmd = ["fasterq-dump", "--split-files", "--threads", "4", sra_path, "-O", srr_dir]
        try:
            subprocess.run(conv_cmd, check=True, text=True)
        except subprocess.CalledProcessError as e:
            log_message(f"fasterq-dump failed for {run_id}: {e}", level="ERROR")
            continue
        
        # Determine layout
        if runinfo_dict is not None:
            layout = runinfo_dict.get(run_id, "SINGLE")
        else:
            layout = "SINGLE"
        layout = layout.upper()

        # If single-end, rename *_1.fastq to .fastq
        if layout == "PAIRED":
            log_message(f"{run_id}: Paired-end data – FASTQ files split into _1 and _2.")
        else:
            # SINGLE
            single_fastq = os.path.join(srr_dir, f"{run_id}_1.fastq")
            target_fastq = os.path.join(srr_dir, f"{run_id}.fastq")
            if os.path.exists(single_fastq):
                os.rename(single_fastq, target_fastq)
                log_message(f"{run_id}: Single-end data – renamed '{run_id}_1.fastq' to '{run_id}.fastq'.")

        # Optionally remove the .sra file to save space
        # os.remove(sra_path)
        # log_message(f"Removed {sra_path}")

def main():
    parser = argparse.ArgumentParser(description="Convert SRA to FASTQ in nested directories, with dynamic single/paired logic.")
    parser.add_argument("--base_dir", required=True, help="Base directory containing GSE folders.")
    parser.add_argument("--gse_id", required=True, help="GSE ID (e.g., GSE12345).")
    parser.add_argument("--run_ids", nargs="+", required=True, help="List of SRR run IDs.")
    parser.add_argument("--paired", action="store_true", help="If set, force all runs as paired-end (unless CSV says otherwise).")
    parser.add_argument("--runinfo_csv", help="Optional path to CSV with columns 'Run' and 'LibraryLayout'. If provided, uses its data.")
    args = parser.parse_args()

    # Read optional CSV
    runinfo_dict = {}
    if args.runinfo_csv:
        runinfo_dict = read_runinfo_csv(args.runinfo_csv)

    # If user gave --paired, override missing entries to PAIRED
    if args.paired:
        for rid in args.run_ids:
            if rid not in runinfo_dict:
                runinfo_dict[rid] = "PAIRED"
    
    # For any run ID not listed in the CSV, default to SINGLE
    for rid in args.run_ids:
        if rid not in runinfo_dict:
            runinfo_dict[rid] = "SINGLE"

    convert_sra_to_fastq(args.run_ids, args.base_dir, args.gse_id, runinfo_dict=runinfo_dict)

if __name__ == "__main__":
    main()
