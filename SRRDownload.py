import os
import subprocess
import sys
import pandas as pd
from utils import log_message, create_directory

class SRRDownload:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def download_srrs(self, geo_dirs: list) -> None:
        """
        Download SRR files for a list of GEO directories.
        """
        for geo_dir in geo_dirs:
            self._log_and_print(f"Processing GEO directory: {geo_dir}")
            srr_csv_file = os.path.join(geo_dir, f"{geo_dir.split('/')[-1]}_SRR.csv")
            runinfo_file = os.path.join(geo_dir, "SRA_RunInfo.csv")

            # Check if SRA_RunInfo.csv exists
            if os.path.exists(runinfo_file) and not os.path.exists(srr_csv_file):
                self._log_and_print(f"Creating {srr_csv_file} from {runinfo_file}...")
                self.create_srr_csv_from_runinfo(runinfo_file, srr_csv_file)
            elif os.path.exists(srr_csv_file):
                self._log_and_print(f"Using existing SRR CSV file: {srr_csv_file}")
                srr_ids = self.read_srr_ids(srr_csv_file)
            else:
                self._log_and_print(f"Neither {runinfo_file} nor {srr_csv_file} exists. Skipping {geo_dir}.")
                continue

            # Download SRR files using prefetch
            for srr_id in srr_ids:
                self._log_and_print(f"Fetching SRR {srr_id}...")
                srr_output_dir = create_directory(os.path.join(geo_dir, srr_id))

                try:
                    prefetch_command = ["prefetch", srr_id, "-O", srr_output_dir]
                    subprocess.run(prefetch_command, check=True, text=True, stdout=sys.stdout, stderr=sys.stderr)
                    self._log_and_print(f"Successfully fetched {srr_id}.")
                except subprocess.CalledProcessError as e:
                    self._log_and_print(f"Error downloading {srr_id}: {e}", level="ERROR")

    def create_srr_csv_from_runinfo(self, runinfo_file: str, srr_csv_file: str) -> None:
        """Create SRR CSV file from SRA_RunInfo.csv."""
        try:
            runinfo_df = pd.read_csv(runinfo_file)
            srr_ids = runinfo_df["Run"].tolist()
            srr_df = pd.DataFrame(srr_ids, columns=["Run"])
            srr_df.to_csv(srr_csv_file, index=False)
            self._log_and_print(f"Created {srr_csv_file} with SRR IDs.")
        except Exception as e:
            self._log_and_print(f"Error creating {srr_csv_file}: {e}", level="ERROR")

    def read_srr_ids(self, file_path: str) -> list:
        """Read SRR IDs from a file."""
        with open(file_path, "r") as f:
            return [line.strip() for line in f if line.strip()]

    def _log_and_print(self, message: str, level: str = "INFO") -> None:
        """Logs message and prints to stdout immediately for real-time visibility."""
        log_message(message, level)
        print(message, flush=True)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python SRRDownload.py <base_dir> <geo_dir1> <geo_dir2> ...")
        sys.exit(1)

    base_dir = sys.argv[1]
    geo_dirs = sys.argv[2:]

    srr_downloader = SRRDownload(base_dir)
    srr_downloader.download_srrs(geo_dirs)
