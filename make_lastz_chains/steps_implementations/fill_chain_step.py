"""Fill chains step."""
import shutil
import subprocess
import os
from constants import Constants
from modules.parameters import PipelineParameters
from modules.project_paths import ProjectPaths
from modules.step_executables import StepExecutables
from modules.make_chains_logging import to_log
from modules.error_classes import PipelineSubprocessError
from parallelization.nextflow_wrapper import execute_nextflow_step
from steps_implementations.fill_chain_split_into_parts_substep import randomly_split_chains
from modules.common import check_expected_file


def create_repeat_filler_joblist(params: PipelineParameters,
                                 project_paths: ProjectPaths,
                                 executables: StepExecutables):
    to_log("Creating repeat filler jobs list")
    infill_chain_filenames = os.listdir(project_paths.fill_chain_jobs_dir)
    to_log(f"fGot {len(infill_chain_filenames)} chain files to fill")
    lastz_parameters = f"\"K={params.fill_lastz_k} L={params.fill_lastz_l}\""
    repeat_filler_params = [
        f"--chainMinScore {params.chain_min_score}",
        f"--gapMaxSizeT {params.fill_gap_max_size_t}",
        f"--gapMaxSizeQ {params.fill_gap_max_size_q}",
        f"--scoreThreshold {params.fill_insert_chain_min_score}",
        f"--gapMinSizeT {params.fill_gap_min_size_t}",
        f"--gapMinSizeQ {params.fill_gap_min_size_q}",
    ]
    if params.fill_unmask:
        to_log("Adding --unmask flag")
        repeat_filler_params.append("--unmask")

    f = open(project_paths.repeat_filler_joblist, "w")
    for filename in infill_chain_filenames:
        chainf = os.path.join(project_paths.fill_chain_jobs_dir, filename)
        chainf_out = f"{os.path.join(project_paths.fill_chain_filled_dir, filename)}.chain"
        repeat_filler_command_parts = [
            executables.repeat_filler,
            f"--workdir {project_paths.fill_chain_run_dir}",
            f"--lastz {executables.lastz}",
            f"--axtChain {executables.axt_chain}",
            f"--chainSort {executables.chain_sort}",
            f"-c {chainf}",
            f"-T2 {params.seq_1_dir}",
            f"-Q2 {params.seq_2_dir}",
            *repeat_filler_params,
            f"--lastzParameters {lastz_parameters}",
            "|",
            executables.chain_score,
            f"-linearGap={params.chain_linear_gap}",
            # $scoreChainParameters,
            "stdin",
            params.seq_1_dir,
            params.seq_2_dir,
            "stdout",
            "|",
            executables.chain_sort,
            "stdin",
            chainf_out
        ]
        repeat_filler_command = " ".join(repeat_filler_command_parts)
        f.write(f"{repeat_filler_command}\n")
    f.close()

    to_log(f"Saved {len(infill_chain_filenames)} chain fill jobs to {project_paths.repeat_filler_joblist}")


def merge_filled_chains(params: PipelineParameters,
                        project_paths: ProjectPaths,
                        executables: StepExecutables):
    # files_to_merge = os.listdir(project_paths.fill_chain_filled_dir)
    to_log("Merging filled chains")
    # Create the 'find' command
    find_cmd = ["find", project_paths.fill_chain_filled_dir, "-type", "f", "-name", "*.chain", "-print"]

    # Create the 'chainMergeSort' command
    merge_sort_cmd = [executables.chain_merge_sort, "-inputList=stdin", f"-tempDir={project_paths.kent_temp_dir}"]

    # Create the 'gzip' command
    gzip_cmd = ["gzip", "-c"]

    to_log("Executing the following sequence of commands in a pipe:")
    to_log(find_cmd)
    to_log(merge_sort_cmd)
    to_log(gzip_cmd)
    # Execute the 'find' command and capture its output
    find_process = subprocess.Popen(find_cmd, stdout=subprocess.PIPE)

    # Pipe the output of 'find' to 'chainMergeSort'
    merge_sort_process = subprocess.Popen(merge_sort_cmd, stdin=find_process.stdout, stdout=subprocess.PIPE)

    # Close the stdout of 'find_process'
    find_process.stdout.close()

    # Pipe the output of 'chainMergeSort' to 'gzip'
    with open(project_paths.filled_chain, "wb") as f:
        gzip_process = subprocess.Popen(gzip_cmd, stdin=merge_sort_process.stdout, stdout=f)

    # Close the stdout of 'merge_sort_process'
    merge_sort_process.stdout.close()

    # Wait for processes to complete and check for errors
    find_exit_code = find_process.wait()
    if find_exit_code != 0:
        raise PipelineSubprocessError(f"find_process failed with exit code {find_exit_code}")

    merge_sort_exit_code = merge_sort_process.wait()
    if merge_sort_exit_code != 0:
        raise PipelineSubprocessError(f"merge_sort_process failed with exit code {merge_sort_exit_code}")

    gzip_exit_code = gzip_process.wait()
    if gzip_exit_code != 0:
        raise PipelineSubprocessError(f"gzip_process failed with exit code {gzip_exit_code}")

    # Wait for 'gzip' to finish
    gzip_process.communicate()
    to_log("Merging filled chains done")


def do_chains_fill(params: PipelineParameters,
                   project_paths: ProjectPaths,
                   executables: StepExecutables):
    # 1. jobs preparation
    infill_template = f"{project_paths.fill_chain_jobs_dir}/infill_chain_"
    to_log("Preparing fill jobs")

    # Need to unzip the zipped merged chain first...
    gunzip_cmd = [
        "gunzip",
        "-c",
        project_paths.merged_chain
    ]
    to_log(f"gunzip -c {project_paths.merged_chain} > {project_paths.fill_chain_temp_input}")
    try:
        with open(project_paths.fill_chain_temp_input, "wb") as f:
            subprocess.run(gunzip_cmd, stdout=f, check=True)
    except subprocess.CalledProcessError:
        raise PipelineSubprocessError("gunzip command at do_chains_fill failed")

    randomly_split_chains(project_paths.fill_chain_temp_input, params.num_fill_jobs, infill_template)

    # 2. create and execute fill joblist
    create_repeat_filler_joblist(params, project_paths, executables)

    execute_nextflow_step(
        executables.nextflow,
        params.cluster_executor,
        Constants.NextflowConstants.JOB_MEMORY_REQ,
        params.job_time_req,
        Constants.NextflowConstants.FILL_CHAIN_LABEL,
        project_paths.fill_chain_run_dir,
        params.cluster_queue,
        project_paths.repeat_filler_joblist,
        project_paths.fill_chain_run_dir
    )

    # 3. merge the filled chains
    merge_filled_chains(params, project_paths, executables)

    # 4. do cleanup
    shutil.rmtree(project_paths.fill_chain_jobs_dir)
    shutil.rmtree(project_paths.fill_chain_filled_dir)
    os.remove(project_paths.fill_chain_temp_input)
    check_expected_file(project_paths.filled_chain, "fill_chain")
    to_log("Fill chains step complete")
