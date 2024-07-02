import os
import subprocess
import argparse

class DirectoryError(Exception):
    pass

def run_dcm2niix(dir_in, dir_out):
    command = "dcm2niix -z -o '{}' '{}'".format(dir_out, dir_in)
    subprocess.check_call(command, shell=True)

def delete_unmatched_files(dir_out, keywords):
    for file_name in os.listdir(dir_out):
        file_path = os.path.join(dir_out, file_name)
        
        #Keep only .nii.gz files containing at least one keyword
        if all([
            os.path.isfile(file_path),
            file_name.endswith(".nii.gz"),
            any([k in file_name for k in keywords]),
        ]):
            continue
        
        os.remove(file_path)

def main(dir_in, dir_out, keywords):        
    #The input directory must exist
    assert os.path.isdir(dir_in), "The input directory {} does not exist.".format(dir_in)
    
    #The output directory must exist
    assert os.path.isdir(dir_out), "The output directory {} does not exist.".format(dir_out)
    
    #dcm2niix is executed
    try:
        run_dcm2niix(dir_in, dir_out)
    except subprocess.CalledProcessError as e:
        print("Error running dcm2niix: {}".format(e))
        exit(1)
    except Exception as e:
        print("An unexpected error occurred: {}".format(e))
        exit(1)
    
    delete_unmatched_files(dir_out, keywords)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert DICOM to NIfTI and filter output files by keywords.")
    parser.add_argument('dir_in', type=str, help='Input directory containing DICOM files')
    parser.add_argument('dir_out', type=str, help='Output directory to store NIfTI files')
    parser.add_argument('keywords', nargs='+', help='List of keywords to filter output files')

    args = parser.parse_args()
    
    main(args.dir_in, args.dir_out, args.keywords)