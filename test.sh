#!/bin/bash
#SBATCH --job-name=pair_15
#SBATCH --array=15
#SBATCH -t 1-0
#SBATCH --output=/scratch/tianche5/wms/chains/make_lastz_chains_onPhx/log/slurm_%A.%a.out
#SBATCH --error=/scratch/tianche5/wms/chains/make_lastz_chains_onPhx/log/slurm_%A.%a.err
#SBATCH --mem=20G
#SBATCH -p public
#SBATCH -q public

module load nextflow-25.04.6-gcc-14.2.0-en
module load openjdk-17.0.3_7-4s
module load mamba
source activate make_lastz_chains-2.0.8_base

ls /scratch/tianche5/wms/chains/make_lastz_chains_onPhx/input

# Path to the species list file
species_list="/scratch/tianche5/wms/chains/make_lastz_chains_onPhx/lastz_ref_query_list.txt"

# Extract reference and query species from the species list file
species_pair=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$species_list")
ref_species=$(echo "$species_pair" | cut -f1)
query_species=$(echo "$species_pair" | cut -f2)

genome_dir="/scratch/tianche5/wms/chains/make_lastz_chains_onPhx/input"
working_dir="/scratch/tianche5/wms/chains/make_lastz_chains_onPhx/"
export PATH=/packages/envs/make_lastz_chains-2.0.8_base/bin:$PATH

cd /scratch/tianche5/wms/chains/make_lastz_chains_onPhx/make_lastz_chains/

./make_chains.py -f --project_dir $working_dir/${ref_species}_${query_species}_15_50m \
--cluster_executor slurm \
--cluster_queue public \
--seq1_chunk 50000000 --seq2_chunk 50000000 \
--chaining_memory 50 \
$ref_species $query_species $genome_dir/${ref_species}.allScaffs.genome.WM.fasta \
$genome_dir/${query_species}.allScaffs.genome.WM.fasta \
#if restarting from a failed step, add this flag:  --continue_from_step lastz 
#to keep temp files and the report files, add this flag:  --keep_temp
