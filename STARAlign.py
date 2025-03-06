#!/usr/bin/env python3

import os
import sys
import glob
import subprocess
import argparse

###############################################################################
# STARAlign.py
# ------------
# Recursively searches for single-end FASTQ files in each dataset subdirectory
# (GSEXXXX/SRRXXXX/...) and aligns them to GRCm39 using STAR.
#
# Example usage (automatically invoked by STARAlign.sh):
#   python STARAlign.py --base_dir /nfs/turbo/umms-sihogan/crizza/Data \
#                       --gse_list GSE106973 GSE128003 GSE128074 \
#                       --threads 8
###############################################################################

# Paths to the GRCm39 reference genome index and GTF annotation
GENOME_INDEX = "/nfs/turbo/umms-sihogan/crizza/STAR_INDEX/GRCm39"
ANNOTATION_GTF = "/nfs/turbo/umms-sihogan/crizza/STAR_INDEX/GRCm39/GRCm39.gtf"

def parse_args():
    parser = argparse.ArgumentParser(
        description="Recursively find FASTQ files and align them with STAR to GRCm39."
    )
    parser.add_argument("--base_dir", required=True,
                        help="Base directory containing GSEXXX subdirectories.")
    parser.add_argument("--gse_list", nargs="+", required=True,
                        help="One or more GSE dataset IDs to process (e.g., GSE106973).")
    parser.add_argument("--threads", type=int, default=1,
                        help="Number of CPU threads for STAR (default=1).")
    return parser.parse_args()

def main():
    args = parse_args()
    base_dir = os.path.abspath(args.base_dir)
    gse_list = args.gse_list
    threads = args.threads

    print("==========================================================")
    print(f"[INFO] Base directory: {base_dir}")
    print(f"[INFO] GSE datasets: {', '.join(gse_list)}")
    print(f"[INFO] Using {threads} threads for STAR alignment.")
    print(f"[INFO] Genome index: {GENOME_INDEX}")
    print("==========================================================")

    overall_fail = 0  # track if any alignment fails

    for gse_id in gse_list:
        gse_path = os.path.join(base_dir, gse_id)
        if not os.path.isdir(gse_path):
            print(f"[ERROR] Cannot find directory for {gse_id}: {gse_path}", file=sys.stderr)
            overall_fail += 1
            continue

        print(f"\n[INFO] Processing dataset: {gse_id}")
        # Look for SRR subdirectories in GSE directory
        srr_folders = [
            d for d in os.listdir(gse_path)
            if d.startswith("SRR") and os.path.isdir(os.path.join(gse_path, d))
        ]

        if not srr_folders:
            print(f"[WARNING] No SRR subdirectories found in {gse_path}. Skipping.")
            continue

        for srr_id in sorted(srr_folders):
            srr_dir = os.path.join(gse_path, srr_id)
            print(f"[INFO] Searching for FASTQ files under: {srr_dir}")

            # Recursively gather .fastq or .fastq.gz files
            fastq_paths = glob.glob(os.path.join(srr_dir, "**", "*.fastq"), recursive=True)
            fastq_paths += glob.glob(os.path.join(srr_dir, "**", "*.fastq.gz"), recursive=True)
            fastq_paths.sort()

            if len(fastq_paths) == 0:
                print(f"[WARNING] No FASTQ files found for {srr_id}.")
                continue

            # For single-end SMART-seq2, we typically have one .fastq per sample,
            # but if multiple exist, we pass them all to STAR as single-end reads.
            print(f"[INFO] Found {len(fastq_paths)} FASTQ file(s). Assuming SINGLE-END layout.")

            # Construct the STAR command
            out_prefix = os.path.join(srr_dir, f"{srr_id}_")  # output in SRR folder
            cmd_parts = [
                "STAR",
                f"--runThreadN {threads}",
                f"--genomeDir {GENOME_INDEX}",
                f"--readFilesIn {' '.join(fastq_paths)}",
                f"--outFileNamePrefix {out_prefix}",
                "--outSAMtype BAM Unsorted",       # produce an unsorted BAM
                "--outFilterMultimapNmax 1"        # only unique alignments
            ]

            # If any FASTQ is gzipped, add zcat
            if any(fp.endswith(".gz") for fp in fastq_paths):
                cmd_parts.append("--readFilesCommand zcat")

            star_cmd = " ".join(cmd_parts)
            print(f"[DEBUG] STAR command:\n  {star_cmd}")

            try:
                subprocess.run(star_cmd, shell=True, check=True)
                bam_file = os.path.join(srr_dir, f"{srr_id}_Aligned.out.bam")
                print(f"[INFO] Alignment complete for {srr_id}. Output: {bam_file}")
            except subprocess.CalledProcessError as e:
                overall_fail += 1
                print(f"[ERROR] STAR alignment failed for {srr_id} with exit code {e.returncode}.", file=sys.stderr)
                continue

    if overall_fail > 0:
        print("[ERROR] Some alignments failed. Check the logs for details.")
        sys.exit(1)
    else:
        print("[INFO] All alignments completed successfully.")

if __name__ == "__main__":
    main()
