### Summary: The following script creates an sbatch file to run the function RunSimulation.py for each parameter vector variation.

### Import packages ###
import os
import numpy as np
import pandas as pd
import argparse

### Directory ###
cwd = os.getcwd()
ParentDirectory = os.path.abspath(os.path.join(cwd, "../.."))

### Set up argument parser ###
parser = argparse.ArgumentParser(description="Parse command line arguments for job parameters")
parser.add_argument("--DataType", type=str, default="-1", help="Simulation case number.")
args = parser.parse_args()

### Open ParameterVector ###
ParameterVector = pd.read_csv(os.path.join(cwd, "Data", "ParameterVectors", "ParameterVector" + args.DataType + ".csv"))

### Loop through each row in the DataFrame ###
for i, row in ParameterVector.iterrows():
    
    ## Extract parameters ###
    JobName = row['JobName']
    Data = row['Data']
    Seed = row['Seed']
    TestProportion = row['TestProportion']
    CandidateProportion = row['CandidateProportion']
    SelectorType = row['SelectorType']
    ModelType = row['ModelType']
    UniqueErrorsInput = row['UniqueErrorsInput']
    n_estimators = row['n_estimators']
    regularization = row['regularization']
    RashomonThresholdType = row['RashomonThresholdType']
    RashomonThreshold = row['RashomonThreshold']
    Type = row['Type']
    BatchSize = row["BatchSize"]
    DiversityWeight = row["DiversityWeight"]
    DensityWeight = row["DensityWeight"]
    Output = row['Output']
    Partition = row["Partition"]
    Time = row["Time"]
    Memory = row["Memory"]
    
    # Path for .sbatch files ###
    TargetDirectory = os.path.join(cwd,"Code", "Cluster", Data, "RunSimulations")
    sbatch_file_path = os.path.join(TargetDirectory, f"{JobName}.sbatch")
    
    # Create the .sbatch file content
    sbatch_content = [
        "#!/bin/bash",
        f"#SBATCH --job-name={JobName}",
        f"#SBATCH --partition={Partition}",                                             # [short, medium, long, largemem, or compute]
        "#SBATCH --ntasks=1",
        f"#SBATCH --time={Time}",                                                # [11:59:00, 6-23:59:00]
        f"#SBATCH --mem-per-cpu={Memory}",                                             # [30000, 100000]
        f"#SBATCH -o ClusterMessages/out/myscript_{JobName}_%j.out",
        f"#SBATCH -e ClusterMessages/error/myscript_{JobName}_%j.err",
        "#SBATCH --mail-type=FAIL",                                             # FAIL ALL
        "#SBATCH --mail-user=simondn@uw.edu",
        "",
        "cd ~/RashomonActiveLearning",
        "module load Python",
        "python Code/RunSimulation.py \\",
        f"    --JobName " + JobName +" \\",
        f"    --Data {Data} \\",
        f"    --Seed {Seed} \\",
        f"    --TestProportion {TestProportion} \\",
        f"    --CandidateProportion {CandidateProportion} \\",
        f"    --SelectorType {SelectorType} \\",
        f"    --ModelType {ModelType} \\",
        f"    --UniqueErrorsInput {UniqueErrorsInput} \\",
        f"    --n_estimators {n_estimators} \\",
        f"    --regularization {regularization} \\",
        f"    --RashomonThresholdType {RashomonThresholdType} \\",
        f"    --RashomonThreshold {RashomonThreshold} \\",
        f"    --Type {Type} \\",
        f"    --BatchSize {BatchSize} \\",
        f"    --DiversityWeight {DiversityWeight} \\",
        f"    --DensityWeight {DensityWeight} \\",
        f"    --Output {Output}"
    ]

    # Write content to .sbatch file
    os.makedirs(os.path.dirname(sbatch_file_path), exist_ok=True)  # Ensure directory exists
    with open(sbatch_file_path, "w") as sbatch_file:
        sbatch_file.write("\n".join(sbatch_content))

print("Creation Sbatch files generated successfully.")
