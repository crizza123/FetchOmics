import os
import subprocess
import pandas as pd
from utils import log_message, create_directory

class STARAligner:
    def __init__(self, base_dir):
        """
        Initialize STARAligner with base directory and predefined genome mappings.
        """
        self.base_dir = base_dir
        self.genome_dir_mapping = {
            "Homo sapiens": "/nfs/turbo/umms-sihogan/crizza/STAR_INDEX/GRCh38",
            "Mus musculus": "/nfs/turbo/umms-sihogan/crizza/STAR_INDEX/GRCm39"
        }

    def align_reads(self, accession):
        """
        Perform alignment for a given GEO accession using STAR.
        """
        geo_dir = os.path.join(self.base_dir, accession)
        align_dir = create_directory(os.path.join(geo_dir, "alignments"))
        runinfo_file = os.path.join(geo_dir, f"{accession}_SRA_RunInfo.csv")
        
        if not os.path.exists(runinfo_file):
            log_message(f"RunInfo file missing for {accession}, skipping alignment.", level="ERROR")
            return
        
        # Read run info to determine layout (SINGLE or PAIRED)
        runinfo_df = pd.read_csv(runinfo_file)
        
        if "Run" not in runinfo_df.columns:
            log_message(f"Run column missing in {runinfo_file}, skipping alignment.", level="ERROR")
            return
        
        layout_map = {row["Run"]: row.get("LibraryLayout", "SINGLE") for _, row in runinfo_df.iterrows()}
        
        scientific_name = runinfo_df["ScientificName"].iloc[0] if "ScientificName" in runinfo_df.columns else "Unknown"
        genome_dir = self.genome_dir_mapping.get(scientific_name)
        
        if not genome_dir:
            log_message(f"No genome directory found for {accession} ({scientific_name}). Using default genome directory.", level="WARNING")
            genome_dir = "/nfs/turbo/umms-sihogan/crizza/STAR_INDEX/Default"
        
        for srr_id, layout in layout_map.items():
            srr_dir = os.path.join(geo_dir, srr_id)
            fastq_files = self.get_fastq_files(srr_dir, srr_id, layout)
            
            if not fastq_files:
                log_message(f"No FASTQ files found for {srr_id} ({layout} layout), skipping.", level="WARNING")
                continue
            
            output_prefix = os.path.join(align_dir, srr_id)
            self.run_star(fastq_files, genome_dir, output_prefix, layout)

    def get_fastq_files(self, srr_dir, srr_id, layout):
        """
        Retrieve FASTQ file paths based on read layout.
        """
        if layout.upper() == "PAIRED":
            fastq_1 = os.path.join(srr_dir, f"{srr_id}_1.fastq")
            fastq_2 = os.path.join(srr_dir, f"{srr_id}_2.fastq")
            return [fastq_1, fastq_2] if os.path.exists(fastq_1) and os.path.exists(fastq_2) else None
        else:
            fastq = os.path.join(srr_dir, f"{srr_id}.fastq")
            return [fastq] if os.path.exists(fastq) else None

    def run_star(self, fastq_files, genome_dir, output_prefix, layout):
        """
        Run STAR alignment.
        """
        command = [
            "STAR",
            "--runThreadN", "4",
            "--genomeDir", genome_dir,
            "--readFilesIn", *fastq_files,
            "--outFileNamePrefix", output_prefix,
            "--outSAMtype", "BAM", "SortedByCoordinate"
        ]
        
        if layout.upper() == "PAIRED":
            command.extend(["--readFilesCommand", "cat"])
        
        log_file = f"{output_prefix}_STAR.log"
        with open(log_file, "w") as lf:
            try:
                subprocess.run(command, check=True, stdout=lf, stderr=lf)
                log_message(f"STAR alignment completed for {output_prefix}.")
            except subprocess.CalledProcessError as e:
                log_message(f"Error in STAR alignment: {e}", level="ERROR")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python STARAligner.py <geo_accessions_file>\n")
        print("geo_accessions_file: A text file containing one GEO accession per line.")
        sys.exit(1)
    
    geo_accessions_file = sys.argv[1]
    
    # Read GEO accessions
    with open(geo_accessions_file, "r") as f:
        geo_accessions = [line.strip() for line in f if line.strip()]
    
    aligner = STARAligner("output")
    for accession in geo_accessions:
        aligner.align_reads(accession)
