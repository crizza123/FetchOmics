import os
import sys
import logging
import pandas as pd
from GeoDataset import GeoDataset
from SRRDownload import SRRDownload
from SRRConvert import SRRConvert
from STARAligner import STARAligner
from utils import log_message, create_directory

# Configure logging globally
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def read_geo_accessions(file_path: str) -> list:
    """Read GEO accessions from a file."""
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

def main(geo_accessions_file: str, base_dir: str = "output") -> None:
    """
    Orchestrates the full omics data processing pipeline.
    """
    log_message("Starting full GEO dataset processing pipeline.")

    # Read GEO accessions
    geo_accessions = read_geo_accessions(geo_accessions_file)

    # Initialize components
    geo_dataset = GeoDataset(geo_accessions)
    srr_downloader = SRRDownload(base_dir)
    srr_converter = SRRConvert(base_dir)
    star_aligner = STARAligner(base_dir)

    # Process each GEO accession
    for accession in geo_accessions:
        log_message(f"Processing GEO accession: {accession}")

        # Create directory for accession
        geo_dir = create_directory(os.path.join(base_dir, accession))

        # Fetch metadata
        results = geo_dataset.process_single_accession(accession, base_dir)
        if not results["metadata"]:
            log_message(f"Skipping {accession} due to missing metadata.", level="WARNING")
            continue

        # Get SRR list from metadata
        srr_csv_path = os.path.join(geo_dir, f"{accession}_SRR.csv")
        if not os.path.exists(srr_csv_path):
            log_message(f"Skipping {accession}, missing SRR file.", level="WARNING")
            continue

        srr_df = pd.read_csv(srr_csv_path)
        srr_ids = srr_df["Run"].tolist()

        # Download SRR files
        srr_downloader.download_srrs(srr_ids, geo_dir)

        # Convert SRR files to FASTQ
        srr_converter.convert_srr_to_fastq(srr_ids, accession)

        # Align reads using STAR
        star_aligner.align_reads(accession)

    log_message("Pipeline completed successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <geo_accessions_file>")
        sys.exit(1)

    geo_accessions_file = sys.argv[1]
    main(geo_accessions_file)
