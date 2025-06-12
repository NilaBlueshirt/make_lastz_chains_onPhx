#!/bin/bash
#SBATCH --job-name=test_4
#SBATCH --array=4
#SBATCH -t 3-0
#SBATCH --output=/scratch/username/chains/log/WM_%A.%a.out
#SBATCH --error=/scratch/username/chains/log/WM_%A.%a.err
#SBATCH --mem=50G
#SBATCH -p public
#SBATCH -q public

module load nextflow-23.10.0-pl
module load openjdk-17.0.3_7-4s
module load mamba
source activate make_lastz_chains-2.0.8_base

ls /scratch/username/make_lastz_chains_onPhx/input

# Path to the species list file
species_list="/scratch/username/make_lastz_chains_onPhx/lastz_ref_query_list.txt"

# Extract reference and query species from the species list file
species_pair=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$species_list")
ref_species=$(echo "$species_pair" | cut -f1)
query_species=$(echo "$species_pair" | cut -f2)

genome_dir="/scratch/username/make_lastz_chains_onPhx/input"
working_dir="/scratch/username/make_lastz_chains_onPhx/"
export PATH=/packages/envs/make_lastz_chains-2.0.8_base/bin:$PATH

cd /scratch/username/make_lastz_chains_onPhx/make_lastz_chains/

./make_chains.py -f --project_dir $working_dir/${ref_species}_${query_species}_4_5m \
--cluster_executor slurm \
--cluster_queue public \
--seq1_chunk 5000000 --seq2_chunk 5000000 \
--chaining_memory 50 \
$ref_species $query_species $genome_dir/${ref_species}.allScaffs.genome.WM.fasta \
$genome_dir/${query_species}.allScaffs.genome.WM.fasta \
