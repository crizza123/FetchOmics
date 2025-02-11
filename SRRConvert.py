import os

import subprocess

import sys

import pandas as pd  # Added missing import

import logging

from utils import log_message



# Setup logging to a single aggregated log file

log_file = "srrconvert.log"

logging.basicConfig(

    filename=log_file,

    level=logging.INFO,

    format="%(asctime)s - %(levelname)s - %(message)s",

    filemode="a"

)



class SRRConvert:

    def __init__(self, base_dir):

        """

        Initialize the SRRConvert class with the base directory for GEO accessions.

        """

        self.base_dir = base_dir



    def convert_srr_to_fastq(self, srr_ids, accession):

        """

        Convert downloaded SRA files to FASTQ format.

        """

        geo_dir = os.path.join(self.base_dir, accession)

        

        for srr_id in srr_ids:

            srr_output_base = os.path.join(geo_dir, f"{srr_id}_Fastq")

            srr_subdir = os.path.join(srr_output_base, srr_id)

            sra_file = os.path.join(srr_subdir, f"{srr_id}.sra")



            if not os.path.exists(sra_file):

                self._log_and_print(f"Skipping {srr_id}, no SRA file found in {srr_subdir}.", level="WARNING")

                continue



            self._log_and_print(f"Converting {srr_id} to FASTQ...")



            try:

                fasterq_command = ["fasterq-dump", "--split-files", sra_file, "-O", srr_subdir]

                subprocess.run(fasterq_command, check=True, text=True, stdout=sys.stdout, stderr=sys.stderr)



                single_fastq = os.path.join(srr_subdir, f"{srr_id}_1.fastq")

                if os.path.exists(single_fastq):

                    os.rename(single_fastq, os.path.join(srr_subdir, f"{srr_id}.fastq"))



                os.remove(sra_file)

                self._log_and_print(f"Deleted SRA file for {srr_id} in {srr_subdir}.")

            except subprocess.CalledProcessError as e:

                self._log_and_print(f"Error processing {srr_id}: {e}", level="ERROR")

                continue



    def _log_and_print(self, message, level="INFO"):

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



    with open(geo_accessions_file, "r") as f:

        geo_accessions = [line.strip() for line in f if line.strip()]

    

    srr_converter = SRRConvert(base_dir)

    

    for accession in geo_accessions:

        srr_csv_path = os.path.join(base_dir, accession, "SRR.csv")

        

        if not os.path.exists(srr_csv_path):

            srr_converter._log_and_print(f"Skipping {accession}, missing SRR.csv.", level="WARNING")

            continue

        

        try:

            srr_df = pd.read_csv(srr_csv_path)

            srr_ids = srr_df["Run"].tolist()

        except Exception as e:

            srr_converter._log_and_print(f"Error reading SRR.csv for {accession}: {e}", level="ERROR")

            continue

        

        srr_converter.convert_srr_to_fastq(srr_ids, accession)


