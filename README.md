# make_lastz_chains_onPhx
This repo saves all the scripts for processing the 28 sample pairs on Phx in 2025 from March to May.

The make_lastz_chains folder is the code cloned from the original repo, version 2.8.0, at the time. In the parallelization folder, the nextflow_wrapper.py script has the modifications we added to work with the Phx slurm. It controls the nextflow behaviors. 
More info: https://training.nextflow.io/2.1/basic_training/debugging/#dynamic-resources-allocation

The mamba env can be recreated from the yml file.

<br />

## To process a fresh sample pair
1. Pull down this repo, or the original make_lastz_chains repo but patch the `parallelization/nextflow_wrapper.py` file.
2. Create an input folder and a log folder in this repo folder. Put the input sample pairs in the input folder. Update the `lastz_ref_query_list.txt` if needed; pay attention to the tab/white space in this manifest file. The `cut_fields_separately.sh` was used to clean up white spaces in the manifest file. 
3. Modify the `test.sh` sbatch script. Manually submit three to four sample pairs at a time; too many main jobs running simultaneously would cause some issues for slurm and nextflow.
4. Since the nextflow child jobs are controlled by the wrapper script, extra time or memory flags are not needed here.
5. The smaller the `chunk size`, the larger the count of the nextflow child jobs will be. If a run failed at the `lastz` or the `chain_run` step, consider reducing the chunk size. The recommended chunk size for these runs is 40M for both reference and query sequences.
6. The slurm `.out` file has the nextflow logs, the `.err` file has the main job log, which would be the same as `working_dir/run.log`. Both slurm job files are important to keep.
7. A successful run will have a `.final.chain.gz` file, and `pipeline_parameters.json`, `run.log`, `steps.json`. A failed run will have lots of temp folders in the working directory.

<br />

## To resume a run from the failed step
1. Keep the original working directory of this failed run.
2. Check the `working_dir/steps.json` to find the failed step.
3. Modify the `restart.sh` sbatch script to make sure the working directory name is the same, and also change the keyword for the `--continue_from_step` flag: `partition,lastz,cat,chain_run,chain_merge,fill_chains,clean_chains`
Source: The `readme` file in the https://github.com/hillerlab/make_lastz_chains

<br />

## To resume a run from the clean_chains step
The mamba env created on Phx has the UCSC Kent tools at version 455, which doesn't have some of the newest version's patches. So when the input data is huge, the workflow calls these older Kent tools and gets an Assertion error at the final step, `clean_chain`.

However, the newest version of Kent tools requires a newer `GLIBC`, which Phx doesn't have. The latest version of the Kent binaries has been downloaded in `make_lastz_chains/HL_kent_binaries` and `HL_kent_binaries_bak`; they are not called by the workflow, but they can be used manually. 

In the progress tracking Google sheet, if a sample pair has the note like `manually ran chainCleaner, Assertion error` or `manually ran chainCleaner`, the Kent binary used was `make_lastz_chains/HL_kent_binaries_bak/chainCleaner_bakMay`, as well as the `chainFilter` and the `chainSort` from the mamba env. If the note was `manually ran chainCleaner apptainer,  chainFilter and gzip, done`, Kent binaries are v482 inside a Ubuntu 22.04-based apptainer. A copy of such container is at `/packages/simg/ucsc-kent_v482.sif` on Phx. The `create_apptainer.sh` file here has the commands for building such an apptainer. 

To use such an apptainer to re-run the clean_chains step

1. Request an interactive session with at least 20min and 30G memory.
2. Load `mamba` and activate the env.
3. Check the run.log file in the working directory of this failed run and copy the `chainCleaner` command at the end of the file.
4. Past the copied command in the second line below, then `cd` into the working directory, and run this code block:
```
apptainer exec /packages/simg/chaincleaner.sif chainCleaner \
...
```

5. After the `chainCleaner`, there are two more steps to get the end product:
```
cd temp_chain_run/

chainFilter -minScore=1000 Pseudophryne_corroboree.Crinia_signifera.filled.chain__temp > Pseudophryne_corroboree.Crinia_signifera.filled.chain

gzip -c Pseudophryne_corroboree.Crinia_signifera.filled.chain > Pseudophryne_corroboree.Crinia_signifera.final.chain.gz
```

The `chainCleaner`, `chainFilter` and `gzip` commands are adapted from `make_lastz_chains/make_chains.py` and `make_lastz_chains/steps_implementations/clean_chain_step.py`. The `-c` flag in the `gzip` command is to preserve the input file and ouput the compressed file with a new file name.

More info:
https://github.com/hillerlab/make_lastz_chains/pull/92
https://github.com/hillerlab/make_lastz_chains/issues/66
http://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/
https://github.com/ucscGenomeBrowser/kent
