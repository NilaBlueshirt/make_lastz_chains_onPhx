#!/bin/bash
#SBATCH --job-name=test_makeChains_small_chunk3
#SBATCH --array=16
#SBATCH -t 5-0
#SBATCH --output=/scratch/tianche5/chains/log/WM_%A.%a.out
#SBATCH --error=/scratch/tianche5/chains/log/WM_%A.%a.err
#SBATCH --mem=100G
#SBATCH -p public
#SBATCH -q public

module load nextflow-23.10.0-pl
module load openjdk-17.0.3_7-4s
module load mamba
source activate make_lastz_chains-2.0.8_base


# Path to the species list file
species_list="/scratch/tianche5/chains/lastz_ref_query_list.txt"

# Extract reference and query species from the species list file
species_pair=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$species_list")
ref_species=$(echo "$species_pair" | cut -f1)
query_species=$(echo "$species_pair" | cut -f2)

genome_dir="/scratch/tianche5/chains/input"
working_dir="/scratch/tianche5/chains/"
export PATH=/packages/envs/make_lastz_chains-2.0.8_base/bin:$PATH

cd /scratch/tianche5/chains/make_lastz_chains/

./make_chains.py -f --project_dir $working_dir/${ref_species}_${query_species}_test_small_chunk_WM \
--cluster_executor slurm \
--cluster_queue public \
--seq1_chunk 40000000 --seq2_chunk 40000000 \
--chaining_memory 100 --job_time_req 00:30:00 \
$ref_species $query_species $genome_dir/${ref_species}.allScaffs.genome.WM.fasta \
$genome_dir/${query_species}.allScaffs.genome.WM.fasta
