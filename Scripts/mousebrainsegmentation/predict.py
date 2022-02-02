
#This script is used to invoke various methods to organize data and perform skull stripping and PF segmentation
from process import read_raw_images_invivo_non_unf, read_raw_images_invivo_unf,post_process_segmentation, post_process_segmentation_PF
from process import fetch_files_validation
import os,sys
from train_brain import config, fetch_mouse_data_files
from unet3d.prediction import run_validation_cases
from unet3d.data import write_data_to_file
from unet3d.utils.utils import pickle_dump
import nibabel as nib
from nilearn.image import resample_to_img
import time, glob
def main(model_path,output_dir, source_path, input_dir,original_voxel_resolutions,foldername,is_diff_fold_struct, model_type,new_spacing,size,view,log_files,is_PF):
    #create output and temporary directories
     
    if not os.path.exists(output_dir+"raw_images"):
        os.makedirs(output_dir+"raw_images")
    if not os.path.exists(output_dir+"output"):
        os.makedirs(output_dir+"output")
    if os.path.exists(output_dir+"output/test.h5"):
        os.remove(output_dir+"output/test.h5")
    
    
    #read raw 2D files and create 3D stacks
    isstructured=True
    if  is_diff_fold_struct==0:#if you dont want to create stacks manually
        if model_type=="invivo-1":#non unifor resolution 
            read_raw_images_invivo_non_unf(input_dir,output_dir,foldername,view,log_files)
            isstructured=False
        else :
            read_raw_images_invivo_unf(input_dir,output_dir,foldername,original_voxel_resolutions, new_spacing, size, model_type,view,log_files)
            original_voxel_resolutions=new_spacing
        
    if len(glob.glob(output_dir+"raw_images/*"))>0: 
        input_dir=output_dir+"raw_images/"
        tmp_output_dir=output_dir
        output_dir=output_dir+"output"

        output_label_map =True
        config["model_file"]=model_path
        config["data_file"]=output_dir+"/test.h5"
        config["labels"]=[1]
        config["validation_file"]=output_dir+"/valid.pkl"
        config["no_label_map"]=True
        config["training_modalities"] = ["brain"]
        config["prediction_dir"]=output_dir
        config["output_basename"]="{subject}.nii.gz"
        config["image_shape"] = size
        config["permute"]=False

        #read TEST volumes
        filenames, subject_ids = fetch_files_validation(input_dir,config["training_modalities"], group="Validation",
                            include_truth=False, return_subject_ids=True)
        if not os.path.exists(config["data_file"]):
            write_data_to_file(filenames, config["data_file"], image_shape=config["image_shape"],
                            subject_ids=subject_ids, save_truth=False,isstructured=isstructured)

            pickle_dump(list(range(len(subject_ids))), config["validation_file"])
        log_files.write("\n")
        log_files.write("File organization is completed: "+" \n")
        log_files.write("Starting Segmentation "+" \n")
        #perform segmentation
        run_validation_cases(validation_keys_file=config["validation_file"],
                             model_file=config["model_file"],
                             training_modalities=config["training_modalities"],
                             labels=config["labels"],
                             hdf5_file=config["data_file"],
                             output_label_map=output_label_map,
                             output_dir=output_dir,
                             test=False,
                             output_basename=config["output_basename"],
                             permute=config["permute"])
        for filename_list, subject_id in zip(filenames, subject_ids):
            prediction_filename = os.path.join(output_dir, config["output_basename"].format(subject=subject_id))
            log_files.write("Resampling: "+ prediction_filename+" \n")
            ref = nib.load(filename_list[0])
            pred = nib.load(prediction_filename)
            pred_resampled = resample_to_img(pred, ref, interpolation="continuous")
            pred_resampled.to_filename(prediction_filename)

        log_files.write("\n")
        log_files.write("Segmentation is completed: "+" \n")
        log_files.write("Starting Postprocessing: "+" \n")
        #perform clean up and post processing
        if is_PF ==False:
            post_process_segmentation(tmp_output_dir,input_dir,original_voxel_resolutions)
        else:
            if model_type=="invivo-1" or model_type=="invivo-2":
                expf=0
            else: expf=1
            post_process_segmentation_PF(tmp_output_dir,input_dir,original_voxel_resolutions,expf)
            
        log_files.write("Post Processing is completed. look at 'final_segmentation' folder "+" \n")
        

if len(os.sys.argv)<9:
    sys.exit()
else:
    args=sys.argv
    model_path=args[1]
    source_path=args[2]
    input_dir=args[3]
    output_dir=args[4]
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    milsec=time.time()
    log_files=open(output_dir+"log_"+str(milsec)+".txt","w")
    log_files.write(".........Parameter received............." +"\n")
    #log_files.write(args +"\n")
    tmp=args[5].strip().split(",")
    log_files.write(args[5].strip() +"\n")
    original_voxel_resolutions=[float(tmp[0].strip()) ,float(tmp[1].strip()) , float(tmp[2].strip()) ]
    foldername=args[6]
    is_diff_fold_struct=int(args[7])
    model_type=args[8]
    view=args[9]


model={}
model["invivo-1"]="brain_unet_model_invivo_non_unf-336.h5"
model["invivo-2"]="brain_unet_model_invivo_unf-300.h5"
model["exvivo-1"]="brain_unet_model_full_cropped-360.h5"
model["exvivo-2"]="brain_unet_model_downsampled-280.h5"
model_path_wb=model_path+model[model_type]

model_resolution={}
model_resolution["invivo-1"]=[1,1,1]
model_resolution["invivo-2"]=[0.06, 0.06, 0.48]
model_resolution["exvivo-1"]=[0.06, 0.06, 0.06]
model_resolution["exvivo-2"]=[0.08, 0.08, 0.08]
new_spacing=model_resolution[model_type]

model_size={}
model_size["invivo-1"]=(320,320,48)
model_size["invivo-2"]=(448,448,48)
model_size["exvivo-1"]=(256, 224, 288)# will be cropped to this(256, 224, 288)
model_size["exvivo-2"]=(256, 224, 256)# will be cropped to this(256, 224, 256)
size=model_size[model_type]

   
#main method
is_PF=False
main(model_path_wb,output_dir,source_path,input_dir,original_voxel_resolutions,foldername,is_diff_fold_struct, model_type, new_spacing,size,view,log_files,is_PF)

#call to segment outer paraflocculus
if model_type=="exvivo-1" or model_type=="exvivo-2" :
    model_path_pf=model_path+"brain_unet_model_exvivo_pf.h5"
    new_spacing=[0.06, 0.06, 0.06]
    size=(256, 224, 288)
    output_dir=output_dir+"PF_outer_"
    is_PF=True
    model_type="exvivo-1"
    main(model_path_pf,output_dir,source_path,input_dir,original_voxel_resolutions,foldername,is_diff_fold_struct, model_type, new_spacing,size,view,log_files,is_PF)
    #post_process_segmentation_PF(output_dir,output_dir+"raw_images/",original_voxel_resolutions)
else:
    model_path_pf=model_path+"brain_unet_model_exvivo_pf.h5"
    new_spacing=[0.06, 0.06, 0.06]
    size=(256, 224, 288)
    output_dir=output_dir+"PF_outer_"
    is_PF=True
    model_type="exvivo-1"
    main(model_path_pf,output_dir,source_path,input_dir,original_voxel_resolutions,foldername,is_diff_fold_struct, model_type, new_spacing,size,view,log_files,is_PF)
    #post_process_segmentation_PF(output_dir,output_dir+"raw_images/",original_voxel_resolutions)
    '''
    model_path_pf=model_path+"brain_unet_model_invivo_pf_306.h5"
    new_spacing=[0.06, 0.06, 0.48]
    size=(448,448,48)
    output_dir=output_dir+"PF_outer_"
    is_PF=True
    model_type="invivo-2"
    main(model_path_pf,output_dir,source_path,input_dir,original_voxel_resolutions,foldername,is_diff_fold_struct, model_type, new_spacing,size,view,log_files,is_PF)
    #post_process_segmentation_PF(output_dir,output_dir+"raw_images/",original_voxel_resolutions)
    '''
log_files.close()





