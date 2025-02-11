import os
import subprocess
import sys
import pandas as pd
import logging
import shutil
from utils import log_message, create_directory

# Setup logging to a single aggregated log file
log_file = "srrconvert.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)

class SRRConvert:
    def __init__(self, base_dir: str, max_retries: int = 3):
        """
        Initialize the SRRConvert class with the base directory for GEO accessions.
        """
        self.base_dir = base_dir
        self.max_retries = max_retries

        # Check if fasterq-dump is installed
        if not shutil.which("fasterq-dump"):
            log_message("Error: fasterq-dump is not installed. Please install it before running this script.", level="ERROR")
            raise FileNotFoundError("fasterq-dump not found in system PATH.")

    def convert_srr_to_fastq(self, srr_ids: list, accession: str) -> None:
        """
        Convert downloaded SRA files to FASTQ format.
        """
        geo_dir = os.path.join(self.base_dir, accession)

        if not os.path.exists(geo_dir):
            log_message(f"Skipping conversion for {accession}, directory does not exist.", level="ERROR")
            return

        for srr_id in srr_ids:
            srr_output_dir = create_directory(os.path.join(geo_dir, srr_id))
            sra_file = os.path.join(srr_output_dir, f"{srr_id}.sra")

            # Check for existing FASTQ files
            fastq_1 = os.path.join(srr_output_dir, f"{srr_id}_1.fastq")
            fastq_2 = os.path.join(srr_output_dir, f"{srr_id}_2.fastq")
            single_fastq = os.path.join(srr_output_dir, f"{srr_id}.fastq")

            if os.path.exists(single_fastq) or os.path.exists(fastq_1):
                log_message(f"Skipping conversion for {srr_id}, FASTQ files already exist.", level="INFO")
                continue

            if not os.path.exists(sra_file):
                log_message(f"Skipping {srr_id}, no SRA file found in {srr_output_dir}.", level="ERROR")
                continue

            log_message(f"Converting {srr_id} to FASTQ...")

            # Retry logic for conversion failures
            for attempt in range(1, self.max_retries + 1):
                try:
                    fasterq_command = ["fasterq-dump", "--split-files", sra_file, "-O", srr_output_dir]
                    subprocess.run(fasterq_command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    # Verify that at least one FASTQ file was created
                    if os.path.exists(fastq_1) or os.path.exists(single_fastq):
                        break  # Exit loop if successful
                except subprocess.CalledProcessError as e:
                    log_message(f"Attempt {attempt}: Failed to convert {srr_id}. Retrying...", level="WARNING")

            # Handle single-end vs paired-end renaming
            if os.path.exists(fastq_1) and not os.path.exists(fastq_2):
                os.rename(fastq_1, single_fastq)
                log_message(f"Converted {srr_id} as SINGLE-END.", level="INFO")

    def read_geo_accessions(self, file_path: str) -> list:
        """Read GEO accessions from a .txt file."""
        with open(file_path, "r") as f:
            return [line.strip() for line in f if line.strip()]

    def _log_and_print(self, message: str, level: str = "INFO") -> None:
        """
        Logs message to both the console and an aggregated log file.
        """
        log_message(message, level)
        print(message, flush=True)
        if level == "ERROR":
            logging.error(message)
        elif level == "WARNING":
            logging.warning(message)
        else:
            logging.info(message)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python SRRConvert.py <geo_accessions_file> <base_dir>")
        sys.exit(1)
    
    geo_accessions_file = sys.argv[1]
    base_dir = sys.argv[2]

    srr_converter = SRRConvert(base_dir)
    
    geo_accessions = srr_converter.read_geo_accessions(geo_accessions_file)
    
    for accession in geo_accessions:
        srr_csv_path = os.path.join(base_dir, accession, f"{accession}_SRR.csv")
        
        if not os.path.exists(srr_csv_path):
            srr_converter._log_and_print(f"Skipping {accession}, missing {accession}_SRR.csv.", level="WARNING")
            continue
        
        try:
            srr_df = pd.read_csv(srr_csv_path)
            srr_ids = srr_df["Run"].tolist()
        except Exception as e:
            srr_converter._log_and_print(f"Error reading {accession}_SRR.csv for {accession}: {e}", level="ERROR")
            continue
        
        srr_converter.convert_srr_to_fastq(srr_ids, accession)
