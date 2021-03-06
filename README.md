# DeepBrainIPP: An end-to-end pipeline for automated mouse brain structures segmentation and morphology analysis.

## Background
DeepBrainIpp is a pipeline for automated skull stripping, brain structures segmentation and morphogenetic characterization. People with/without technical expertise can use DeepBrainIPP. For Non-computational research staff a system administrator can setup four components (Web Application, Job Manager, Singularity Repository, Computing Node) of DeepBrainIPP to access it via web browser. However, DeepBrainIPP can be used from command prompt/terminal too. **Clone the project with LFS git before using it**. Please send us an email to get pass key for accessing our dataset.


![skull stripping](misc/3.jpg?raw=true "Skull Stripping")

## Hardware and software requirements for model inference and training
1. Supported GPU: NVIDIA DGX 
2. Nvidia Driver 450.80.02
3. CUDA Version: 11.0
4. Python 3.6+
5. Tensorflow, keras
6. Singularity: all the necessary requirements are listed in Singularity recipie file
7. LFS git
8. follow this guide https://sylabs.io/guides/3.0/user-guide/installation.html to install singularity
9. Dataset is available at http://ftp.stjude.org/pub/CBI_Bioimage_Data/DeepBrainIPP.tar.gz.gpg
10. Two singularity images are available at http://ftp.stjude.org/pub/CBI_Bioimage_Data/materials.tar.gz.gpg

## User guide for inference

### Accessing DeepBrainIPP from command prompt (does not require setting up IPP)

#### Skull Stripping (Figure 1. Step 1-2 in draft manuscript ) and Paraflocculus Segmentation (Figure 1. Branch II ) 
-----
        1.  Clone the project with LFS git and Build singularity images using the recipe provided in "Singularity" folder
            
            sudo singularity build skull_stripping.img skull_stripping_recipie.def
            
        2.  Make sure your input MRI volumes are in separate folders. MRIs can be 3D stacks or seriese of slice. see Example dataset for details. We have also uploded few in vivo TEST MRI volumes   
        
            folder_name1/prefix_name1_*.nii.gz
            folder_name2/prefix_name2_*.nii.gz
            
        3.  Enter necessary parameters in "config.json" file located in "Singularity" folder. The config file has following parameter:
        
            a. input_dir: Absolute path of your input MRI volumes. For example, to use our Example dataset you can set path like below. 
              
              "input_dir": "{cloned path}/DeepBrainIPP/Example_Dataset/input_volumes/"
            
            b. foldername: prefix/pattern of the MRI volumes name. For example, our Example dataset contains two MRI volumes and they are in two separate folders,
               "ID_GOP87", "ID_5647". Both MRI volumes have prefix "ID_*".
            
              "foldername": "ID_",
            
            c. output_dir: The absolute path where you want to store the segmentation outcome.
            
              "output_dir": "{cloned path}/DeepBrainIPP/Example_Dataset/segmentation_outcome/", 
            
            d. source_path: Where you cloned the code. Absolute path of "DeepBrainIPP" folder
            
              "source_path": "{cloned path}/DeepBrainIPP", 
            
            
            e. model: Absolute path of folder that contains the models after you clone the project
            
              "model": "{cloned path}/DeepBrainIPP/Models/", 
            
            f. is_diff_fold_struct: This can be used when you want to manually organize file.
              
              "is_diff_fold_struct": 0.0
             
            g. model_type: You need to select models based on the resolution of your MRI volumes that requires less interpolation to match with
            models. For our Example dataset use "exvivo-1" and in vivo MRIs use "invivo-2". 
              
              invivo-2: 0.06mm X 0.06mm X 0.48mm
              exvivo-1: 0.06mm X 0.06mm X 0.06mm
              exvivo-2: 0.08mm X 0.08mm X 0.08mm,
              
            h. original_voxel_resolutions: Resolution of your MRIs
              
              "original_voxel_resolutions": "0.06,0.06,0.06"
            i. view: This is for reslicing volumes
              
              "view": "NO",
             J. ignore the following if you do not use HPC cluster
              
              "cbihosts": "local_machine",
              "gridQueue": "dgx",
              "gridResources": 60000.0
          
        4.  Run singularity image 
        5.  Make sure your MRIs is a coronal scan (back to front) 
            
            singularity run -B [location of data and absolute path of base folder of DeepBrainIPP] --nv  skull_stripping.img config.json
        
        6. Once the process is finished the skull stripped brain will be stored in "final_segmentation" folder and measured volumes will be stored in ".csv" file
        7. Similarly segmented Paraflocculus will be stored in "PF_outer_final_segmentation"

#### Large Brain Region Registration based Segmentation (Figure 1. Step 2-5 in draft manuscript )

-----
        1. Download fiji from https://imagej.net/software/fiji/downloads
        2. Extract it and put in "Singularity" folder
        2. Make Sure fiji runs headlessly
        2.  Build singularity images using the recipe provided in "Singularity" folder. If you are unable to build the singularity image use following link to download it and put "imageprocessing-antswithmasklandmarks-1.0.simg" in "Singularity" folder and skip step bellow.                     
            sudo singularity build imageprocessing-antswithmasklandmarks-1.0.simg antsregistrationbatch.def
            
        2.  Enter necessary parameters in "registration_config.json" file. Specially the following
        
           a. batch: when you have multiple files

               "batch": 1.0,

           b. bind_path
           
              "bind_path": "Bind path to mount data location inside Singularity", 
           
           c. fixed_file: Atlas/template based on ex vivo and in vivo MRIs
              
              "fixed_file": "{cloned path}/DeepBrainIPP/Atlas/ex-vivo_template.nrrd",
           
           d. move_file: folder where skull stripped volumes are stored. 
              
              "move_file": "{cloned path}/DeepBrainIPP/Example_Dataset/segmentation_outcome/final_segmentation/",
           
           e. num_of_thread: Allocate based on your CPU
           
              "num_of_thread": 15.0,
           
           f. operation_type: Define what operation you want to perform. e.g "antsregistration" or "quantifybrain"
           
              "operation_type": "antsregistration", 
           
           g. outputfile: Where you want to save segmented brain structures.
           
              "outputfile": "{cloned path}/DeepBrainIPP/Example_Dataset/segmentation_outcome/Registration_outcomes/", 
           
           h. reg_param: This parameters are directly passed to ANTs. This is MRIs/dataset dependant. However, two sets of parameter is provided in user manual that                 we used for our ex vivo and in vivo image registration
           
              "reg_param": " a sample is given in registration_config.json file or see user manual "
        
        4.  Run singularity image 
            
            singularity run -B [location of data and absolute path of base folder of DeepBrainIPP] imageprocessing-antswithmasklandmarks-1.0.simg registration_config.json
            
        5. Registration process will generate summarized result and put in ".pdf" file for each volume. see a sample https://github.com/stjude/DeepBrainIPP/blob/main/misc/Euler3DTransform_AffineTransform_SyN__1622230132.pdf
       
#### Ex vivo Sub-cerebellar Structure Segmentation (Figure 1. Step 6-8 in draft manuscript ))
-----
       
        1.  Enter necessary parameters in "registration_config.json" file and make "isCerebellum":"1" 
        2.  Run singularity image 
            
            singularity run -B [location of data and absolute path of base folder of DeepBrainIPP] antsregistrationbatch.img registration_config.json

#### Quantifying Segmented Structures to receive measurements in .csv file
-----
       
        2.  Enter necessary parameters in "quantify_structure.json" file.
          
          a. interpolation: interpolation such as linear, or KNN or Spline
          
              "interpolation": "BSpline[3]", 
          
          b. mask: mask associated your atlas or template 
          
              "mask": "{cloned path}/DeepBrainIPP/Atlas/Atlases/ex-vivo_mask.nrrd", 
          
          c. "operation_type": "quantifybrain",
          
          d. original_voxel: Voxel resolution to what MRIs were resampled (depends on choosen models type)
          
              "original_voxel": "0.06,0.06,0.06", 
          
          e outputfile: location where registered volumed are stored
          
              "outputfile": "{cloned path}/DeepBrainIPP/Example_Dataset/segmentation_outcome/Registration_outcomes/wholebrain/",
          
          f. structure: File that contains labels of the structures annotated in the mask
          
              "structure": "{cloned path}/DeepBrainIPP/Atlas/Atlases/ex-vivo_regionmap.txt"

        5.  Run singularity image 
            
            singularity run -B [location of data and absolute path of base folder of DeepBrainIPP] antsregistrationbatch.img quantify_structure.json



  
  ### Accessing DeepBrainIPP from web interface (requires setting up IPP):
 -----
     System administrator: Setting up web application
        1. Setup IPP from https://github.com/JaneliaSciComp/jacs-cm"
        2. Setup singularity registry server from https://singularityhub.github.io/sregistry/docs/setup/#pancakes-installation
        3. Build singularity images using the recipe provided in "Singularity" folder
        4. Upload singularity images to installed singularity registry server
        5. Configure pipeline from the admin section
     Users: Accessing web interface and user manual
        1. Use following guideline https://github.com/stjude/DeepBrainIPP/blob/main/misc/DeepBrainIPP_users_manual_github.pdf


## User Guide for Model Training.
### Please send us an email to get pass key for accessing our dataset.
-----
  1. Download the singularity images from this URL http://ftp.stjude.org/pub/CBI_Bioimage_Data/materials.tar.gz.gpg (You will find two images)
  
  2. Copy them in "Singularity" folder
  
  3. Download dataset from http://ftp.stjude.org/pub/CBI_Bioimage_Data/DeepBrainIPP.tar.gz.gpg and extract it. (You will find 172 MRI volumes)
 
  4. Shell into the singularity image. run following command sequentially
 
        singularity shell -B {project cloned path},{data location} --nv singularity_for_training.simg
        
        cd {project clone path}
  5. Once you are inside the singularity image run following. It will spin up a Jupyter notebook and will show url to access
 
        export JUPYTER_ALLOW_INSECURE_WRITES=true
        
        export JUPYTER_RUNTIME_DIR={directory where you have write access}
        
        jupyter notebook --no-browser
        
  6. open a browser and paste URL with token.     
  7. Navigate to the folder "/Scripts/mousebrainsegmentation/"
  8. open the notebook "data_organization_and_training.ipynb"
  9. Follow step by step process to train the model
 
## Citation

#### Acknowledgement
We would like to thank Ellis et al. because piece of code has been adapted, updated and customized from thier work titled as "Trialing u-net training modifications for segmenting gliomas using open source deep learning framework"
