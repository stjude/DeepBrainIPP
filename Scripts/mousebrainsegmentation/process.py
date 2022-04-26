
import os,glob,sys, shutil
import argparse
import nibabel as nib
from nilearn.image import resample_to_img
from train_brain import config, fetch_mouse_data_files
from unet3d.prediction import run_validation_cases
from unet3d.data import write_data_to_file
from unet3d.utils.utils import pickle_dump
import numpy as np
import scipy.ndimage.morphology as morphology
import scipy.ndimage as ndimage
from medpy.io import load, save
from skimage.measure import label, regionprops 
import SimpleITK as sitk
from skimage import  exposure
import nrrd


def N4_bias_correction(img):
    print("N4 bias correction runs.")
    img = sitk.Cast(img,sitk.sitkFloat32)
    corrector = sitk.N4BiasFieldCorrectionImageFilter();
    corrector.SetMaximumNumberOfIterations([1]*4)
    output_img = corrector.Execute(img)
    output_img=sitk.Cast(output_img,sitk.sitkUInt16)
    return output_img
    
def read_raw_images_invivo_non_unf(raw_volume_path,out_path_after_preprocess,foldername,view,log_files):
    log_files.write(".....Reading files...... \n")
    for dirs in glob.glob(raw_volume_path+"/*"):
        imag_path=dirs
        basename=os.path.basename(dirs)
        file_name=glob.glob(imag_path+"/"+foldername+"*")
        if file_name is not None and len(file_name)>0:
            file_name=file_name[0]
            log_files.write(file_name+" \n")
            img,h=load(file_name)
            if view=="YES":
                img=np.transpose(img,(0,2,1))
                img=np.flip(img, axis=2)
            if not (os.path.exists(out_path_after_preprocess+"raw_images/"+basename)):
                os.makedirs(out_path_after_preprocess+"raw_images/"+basename)
            save(img,out_path_after_preprocess+"raw_images/"+basename+"/"+basename+"_brain.nii.gz",use_compression=True)
    if len(glob.glob(out_path_after_preprocess+"raw_images/*"))==0:
        log_files.write("Could not find any files. Please ckeck the input file and pattern \n")
def resample_volume(volume_path,ismask, new_spacing,size ,out_path,basename,model_type):
    if ismask==1:
        interpolator = sitk.sitkNearestNeighbor
    else:
        interpolator = sitk.sitkBSpline
        
    if model_type=="exvivo-1" or model_type=="exvivo-2":
        size=(448,448,384)
        
    volume = sitk.ReadImage(volume_path) # read and cast to float32
    #bias correction
    #volume=N4_bias_correction(volume)
    
    original_spacing = volume.GetSpacing()
    original_size = volume.GetSize()
    original_direction=volume.GetDirection()
    original_origin=volume.GetOrigin()
    offset_origin=np.subtract(new_spacing, original_spacing)/2
    
    
    new_size = [int(round(osz*ospc/nspc)) for osz,ospc,nspc in zip(original_size, original_spacing, new_spacing)]
    #print(new_size)
    resampled_img=sitk.Resample(volume, new_size, sitk.Transform(), interpolator,
                         original_origin+offset_origin, new_spacing, original_direction, 0,
                         volume.GetPixelID())
    if(os.path.exists(out_path+"res.nii.gz")):
        os.remove(out_path+"res.nii.gz")
    sitk.WriteImage(resampled_img,out_path+"res.nii.gz")
    img,h=load(out_path+"res.nii.gz")
    if(ismask==1):
        img[img>0]=1
    rezized_image=np.zeros(size,dtype=np.uint16)
    img_shapes=img.shape
    center=np.divide(rezized_image.shape,2)
    start_pos=np.divide(img_shapes,2)
    start_pos=center-start_pos
    rezized_image[int(start_pos[0]):int(start_pos[0])+img_shapes[0],int(start_pos[1]):int(start_pos[1])+img_shapes[1],int(start_pos[2]):int(start_pos[2])+img_shapes[2]]=img
    if (not os.path.exists(out_path+"inex_train/"+basename)):
        os.makedirs(out_path+"inex_train/"+basename)
    filename=os.path.basename(volume_path)
    
    if model_type=="exvivo-1":
        thresholds=(128,112,144,0)
        rezized_image=crop_volume(rezized_image,thresholds)
    elif model_type=="exvivo-2":
        thresholds=(128,112,128,0)
        rezized_image=crop_volume(rezized_image,thresholds)
    
    save(rezized_image,out_path+"inex_train/"+basename+"/"+filename,hdr=h,use_compression=False)

def crop_volume(img,thresholds):
    center_mass=ndimage.measurements.center_of_mass(img)   
    x=int(center_mass[0]-thresholds[0])
    y=int(center_mass[1]-thresholds[1])+thresholds[3]
    z=int(center_mass[2]-thresholds[2])
    if x<0:
        x=0
    if y<0:
        y=0
    if z<0:
        z=0
    img=img[x:x+2*thresholds[0],y:y+2*thresholds[1],z:z+2*thresholds[2]]
    return img

def crop_volume_invivo(img,thresholds):
    tmp_img=np.zeros((thresholds[0],thresholds[1],thresholds[2]),dtype=img.dtype)
    
    center_mass=ndimage.measurements.center_of_mass(img)   
    x=int(center_mass[0]-thresholds[0])
    y=int(center_mass[1]-thresholds[1])+thresholds[3]
    z=int(center_mass[2]-thresholds[2])
    if x<0:
        x=0
    if y<0:
        y=0
    if z<0:
        z=0
    
    tmp_img[:img.shape[0],:img.shape[1],:img.shape[2]]=img
    return tmp_img

def read_raw_images_invivo_unf(raw_volume_path,out_path_after_preprocess,foldername,original_voxel_resolutions, new_spacing, size, model_type,view,log_files):
    log_files.write(".....Reading files...... \n")
    for dirs in glob.glob(raw_volume_path+"*"):
        for files in glob.glob(dirs+"/"+foldername+"*"):
            log_files.write(files+" \n")
            basename=os.path.basename(dirs)
            imag_path=files
            img,h=load(imag_path)
            if view=="YES":
                img=np.transpose(img,(0,2,1))
                img=np.flip(img, axis=2)
                
            #img=img[:,:,::-1]
            h.set_voxel_spacing(original_voxel_resolutions)
            if not (os.path.exists(out_path_after_preprocess+"raw_images/"+basename)):
                os.makedirs(out_path_after_preprocess+"raw_images/"+basename)
            save(img,out_path_after_preprocess+"raw_images/"+basename+"/"+basename+"_brain.nii.gz", hdr=h,use_compression=False)
            imag_path=out_path_after_preprocess+"raw_images/"+basename+"/"+basename+"_brain.nii.gz"
            resample_volume(imag_path,0,new_spacing,size,out_path_after_preprocess,basename,model_type)
    if len(glob.glob(out_path_after_preprocess+"raw_images/*"))==0:
        log_files.write("Could not find any files. Please ckeck the input file and pattern \n")
    else:
        shutil.rmtree(out_path_after_preprocess+"raw_images")
        os.rename(out_path_after_preprocess+"inex_train", out_path_after_preprocess+"raw_images")

def fetch_files_validation(input_dir,modalities, group="Validation", include_truth=False, return_subject_ids=False):
    training_data_files = list()
    subject_ids = list()
    modalities = list(modalities)
    if include_truth:
        modalities = modalities + ["seg"]
    #print(os.path.join(os.path.dirname(files_dir), "data", "*{0}*", "*{0}*").format(group))
    for subject_dir in glob.glob(input_dir+"/*"):
        subject_id = os.path.basename(subject_dir)
        
        subject_ids.append(subject_id)
        subject_files = list()
        for modality in modalities:
            subject_files.append(os.path.join(subject_dir, subject_id + "_" + modality + ".nii.gz"))
            #print(os.path.join(subject_dir, subject_id + "_" + modality + ".nii.gz"))
        training_data_files.append(tuple(subject_files))
    if return_subject_ids:
        return training_data_files, subject_ids
    else:
        return training_data_files
    
def post_process_segmentation(out_path_after_preprocess,raw_volume_path, original_voxel_resolutions):

    input_path=out_path_after_preprocess+"/output/"
    output_path=out_path_after_preprocess+"/final_segmentation/"
    measurements_file=out_path_after_preprocess+"/final_segmentation/brain_measures.csv"
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    with open(measurements_file,'w') as m_file:
        m_file.write("Volume Id, Whole Brain Volume \n")

        for files in glob.glob(input_path+"/*.nii.gz"):
            print(files)
            img,h=load(files)
            img[img>0.2]=1.0
            tmp_img=np.zeros_like(img)
            filename=os.path.basename(files).split(".")[0]
            for i in range(img.shape[2]):
                label_img=label(img[:,:,i], neighbors=4)
                tmp_slice=np.zeros_like(img[:,:,i])
                for region in regionprops(label_img):
                    if region.area>500:
                        cords=region.coords
                        tmp_slice[cords[:,0],cords[:,1]]=1.0
                tmp_slice=morphology.binary_closing(tmp_slice).astype(np.int32)
                tmp_img[:,:,i]=tmp_slice
            voxel_res=h.get_voxel_spacing()
            print(voxel_res)
            tmp_img=ndimage.binary_fill_holes(tmp_img)
            tmp_img=morphology.binary_closing(tmp_img).astype(np.int32)
            volumes=np.count_nonzero(tmp_img)*original_voxel_resolutions[0]*original_voxel_resolutions[1]*original_voxel_resolutions[2]
            m_file.write(filename+","+str(volumes)+"\n")
            segmented_img,rh=load(raw_volume_path+filename+"/"+filename+"_brain.nii.gz")
            segmented_img[tmp_img!=1.0]=0
            h.set_voxel_spacing(original_voxel_resolutions)
            save(tmp_img,output_path+filename+"_seg.nii.gz", hdr=h, use_compression=False)
            save(segmented_img,output_path+filename+"_segmented_brain.nrrd", hdr=h, use_compression=False)
            #nrrd_image, header=nrrd.read(output_path+filename+"_segmented_brain.nrrd")
            #header["units"]=['mm', 'mm', 'mm']
            #nrrd.write(output_path+filename+"_segmented_brain.nrrd", nrrd_image, header)

def post_process_segmentation_PF(out_path_after_preprocess,raw_volume_path, original_voxel_resolutions, expf):


    input_path=out_path_after_preprocess+"output/"
    output_path=out_path_after_preprocess+"final_segmentation/"
    measurements_file=out_path_after_preprocess+"final_segmentation/brain_measures.csv"
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    with open(measurements_file,'w') as m_file:
        m_file.write("Volume Id, PF Volume \n")

        for files in glob.glob(input_path+"/*.nii.gz"):
            filename=os.path.basename(files).split(".")[0]
            print(files)
            img,h=load(files)
            segmented_img,rh=load(raw_volume_path+filename+"/"+filename+"_brain.nii.gz")
            #img[img>0.2]=1.0
            tmp_img=np.zeros_like(img)
            #img=ndimage.binary_fill_holes(tmp_img)
            label_img=label(img)
            region_cnt=0
            for region in sorted(regionprops(label_img),key=lambda r: r.area,reverse=True):
                region_cnt+=1
                if region.area>100 and region_cnt<=2:
                    cords=region.coords
                    tmp_img[cords[:,0],cords[:,1],cords[:,2]]=1.0
            if expf==1:
                tmp_img[segmented_img<85]=0 #85
            else:
                tmp_img[segmented_img<10]=0 
            voxel_res=h.get_voxel_spacing()
            print(voxel_res)
            tmp_img=ndimage.binary_opening(tmp_img).astype(np.int32)
            tmp_img=ndimage.binary_fill_holes(tmp_img).astype(np.int32)

            img=tmp_img
            tmp_img=np.zeros_like(img)
            for i in range(img.shape[2]):
                label_img=label(img[:,:,i], neighbors=4)
                tmp_slice=np.zeros_like(img[:,:,i])
                region_cnt=0
                for region in sorted(regionprops(label_img),key=lambda r: r.area,reverse=True):
                    region_cnt+=1
                    if region.area>10 and region_cnt<=2:
                        cords=region.coords
                        tmp_slice[cords[:,0],cords[:,1]]=1.0
                tmp_slice[segmented_img[:,:,i]==0]=0
                tmp_slice=morphology.binary_fill_holes(tmp_slice).astype(np.int32)
                tmp_img[:,:,i]=tmp_slice


            img=tmp_img
            tmp_img=np.zeros_like(img)
            #img=ndimage.binary_fill_holes(tmp_img)
            label_img=label(img)
            region_cnt=0
            for region in sorted(regionprops(label_img),key=lambda r: r.area,reverse=True):
                region_cnt+=1
                if region.area>100 and region_cnt<=2:
                    cords=region.coords
                    tmp_img[cords[:,0],cords[:,1],cords[:,2]]=1.0

            tmp_img=morphology.binary_closing(tmp_img).astype(np.int32)
            volumes=np.count_nonzero(tmp_img)*original_voxel_resolutions[0]*original_voxel_resolutions[1]*original_voxel_resolutions[2]
            m_file.write(filename+","+str(volumes)+"\n")

            segmented_img[tmp_img!=1.0]=0
            h.set_voxel_spacing(original_voxel_resolutions)
            save(tmp_img,output_path+filename+"_seg.nii.gz", hdr=h, use_compression=False)
            save(segmented_img,output_path+filename+"_segmented_PF.nrrd", hdr=h, use_compression=False)



