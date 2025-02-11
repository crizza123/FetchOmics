import os
import logging
import subprocess
import requests
import time
from multiprocessing import BoundedSemaphore

# Global configuration
global_request_semaphore = BoundedSemaphore(3)  # Limit to 3 concurrent requests

# Configure logging globally
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def log_message(message: str, level: str = "INFO") -> None:
    """
    Log a message with a specified logging level.
    """
    levels = {
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR
    }
    logging.log(levels.get(level, logging.INFO), message)

def create_directory(path: str) -> str:
    """
    Create a directory at the specified path.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return path
    except Exception as e:
        log_message(f"Error creating directory {path}: {e}", level="ERROR")
        return None

def fetch_numeric_id(accession: str, email: str = "your_email@example.com", tool: str = "FetchOmics",
                     api_key: str = None, max_retries: int = 10, delay: int = 5) -> str:
    """
    Fetch the numeric ID for a given accession from the NCBI E-utilities.
    """
    params = {
        "db": "gds",
        "term": f"{accession}[Accession]",
        "retmode": "json",
        "email": email,
        "tool": tool
    }

    # Include API key if provided
    if api_key:
        params["api_key"] = api_key

    for attempt in range(1, max_retries + 1):
        try:
            with global_request_semaphore:  # Limit concurrent requests
                response = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params=params)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", delay))
                log_message(f"Rate limit exceeded (Attempt {attempt}). Retrying in {retry_after} seconds...")
                time.sleep(retry_after)
                continue

            response.raise_for_status()
            data = response.json()
            id_list = data.get("esearchresult", {}).get("idlist", [])

            if id_list:
                log_message(f"Accession: {accession}, First GDS ID: {id_list[0]}")
                time.sleep(0.34)  # Ensure at most 3 requests per second
                return id_list[0]
            else:
                log_message(f"Accession: {accession}, No GDS ID found.", level="WARNING")
                return None

        except requests.exceptions.RequestException as e:
            log_message(f"Attempt {attempt}: Error fetching numeric ID for {accession}: {e}", level="WARNING")
            if attempt < max_retries:
                backoff_time = delay * (2 ** (attempt - 1))
                log_message(f"Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)
            else:
                log_message(f"Max retries reached for {accession}.", level="ERROR")
                return None

def fetch_runinfo(gds_id: str, output_dir: str, max_retries: int = 10, delay: int = 5) -> str:
    """
    Fetch RunInfo for a given GDS ID and save it to the specified output directory.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{gds_id}_SRA_RunInfo.csv")

    command = (
        f"elink -db gds -id {gds_id} -target sra | "
        f"efetch -format runinfo > {output_file}"
    )

    for attempt in range(1, max_retries + 1):
        try:
            with global_request_semaphore:
                subprocess.run(command, shell=True, check=True, text=True)

            log_message(f"RunInfo for GDS ID {gds_id} saved to {output_file}")
            time.sleep(0.34)  # Ensure at most 3 requests per second
            return output_file

        except subprocess.CalledProcessError as e:
            log_message(f"Attempt {attempt}: Error fetching RunInfo for GDS ID {gds_id}: {e}", level="WARNING")
            if attempt < max_retries:
                backoff_time = delay * (2 ** (attempt - 1))
                log_message(f"Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)
            else:
                log_message(f"Max retries reached for GDS ID {gds_id}.", level="ERROR")
                return None
