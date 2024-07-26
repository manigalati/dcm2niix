import os
import subprocess
import argparse
import nibabel as nib
import numpy as np

class DirectoryError(Exception):
    pass

def run_dcm2niix(dir_in, dir_out, extra_options):
    command = "dcm2niix {} -o '{}' '{}'".format(extra_options, dir_out, dir_in)
    subprocess.check_call(command, shell=True)

def delete_unmatched_files(dir_out, keywords):
    for file_name in os.listdir(dir_out):
        file_path = os.path.join(dir_out, file_name)
        
        #Keep only .nii.gz files containing at least one keyword
        if all([
            os.path.isfile(file_path),
            file_name.endswith(".nii.gz"),
            any([k.lower() in file_name.lower() for k in keywords]),
        ]):
            continue
        
        os.remove(file_path)

def process_swi(dir_out, print_shape=False):
    images_ph = [f for f in os.listdir(dir_out) if "swi" in f.lower() and f.endswith("ph.nii.gz")]
    images_mg = [f for f in os.listdir(dir_out) if "swi" in f.lower() and not f.endswith("ph.nii.gz")]
    
    if len(images_ph) == 0 or len(images_mg) == 0:
        print("SWI undetected")
        exit(1)
    
    image_ph = np.zeros([0,0,0])
    for f in images_ph:
        f = nib.load(os.path.join(dir_out, f))
        f, affine, header = f.get_fdata(), f.affine, f.header
        if f.shape[-1] > image_ph.shape[-1]:
            image_ph = f
            image_ph_aff = affine
            image_ph_header = header
        elif f.shape[-1] == image_ph.shape[-1]:
            image_ph += f
    image_ph /= len(images_ph)
    
    image_mg = np.zeros([0,0,0])
    for f in images_mg:
        f = nib.load(os.path.join(dir_out, f))
        f, affine, header = f.get_fdata(), f.affine, f.header
        if f.shape[-1] > image_mg.shape[-1]:
            image_mg = f
            image_mg_aff = affine
            image_mg_header = header
        elif f.shape[-1] == image_mg.shape[-1]:
            image_mg += f
    image_mg /= len(images_mg)
    
    image = image_mg * image_ph**4
    
    nib.save(
        nib.Nifti1Image(image.astype(float), image_mg_aff, image_mg_header),
        os.path.join(dir_out, "swi.nii.gz")
    )
    

def main(dir_in, dir_out, keywords, extra_options):        
    #The input directory must exist
    assert os.path.isdir(dir_in), "The input directory {} does not exist.".format(dir_in)
    
    #The output directory must exist
    assert os.path.isdir(dir_out), "The output directory {} does not exist.".format(dir_out)
    
    #dcm2niix is executed
    try:
        run_dcm2niix(dir_in, dir_out, extra_options)
    except subprocess.CalledProcessError as e:
        print("Error running dcm2niix: {}".format(e))
        exit(1)
    except Exception as e:
        print("An unexpected error occurred: {}".format(e))
        exit(1)
    
    delete_unmatched_files(dir_out, keywords)
    
    if any([k.lower() == "swi" for k in keywords]):
        process_swi(dir_out, print_shape = "PRINTTT" in extra_options)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert DICOM to NIfTI and filter output files by keywords.")
    parser.add_argument('dir_in', type=str, help='Input directory containing DICOM files')
    parser.add_argument('dir_out', type=str, help='Output directory to store NIfTI files')
    parser.add_argument('--keywords', nargs='+', default=[""], help='List of keywords to filter output files')
    parser.add_argument('--extra-options', type=str, default='-z y -m y', help='Additional options to pass to the conversion process')

    args = parser.parse_args()
    
    main(args.dir_in, args.dir_out, args.keywords, args.extra_options)