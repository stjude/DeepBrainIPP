# DeepBrainIPP: An end-to-end pipeline for automated mouse brain structures segmentation and morphology analysis.

## Background
DeepBrainIpp is a pipeline for automated skull stripping, brain structures segmentation and morphogenetic characterization. People with/without technical expertise can use DeepBrainIPP. For Non-computational research staff a system administrator can setup four components (Web Application, Job Manager, Singularity Repository, Computing Node) of DeepBrainIPP to access it via web browser. However, DeepBrainIPP can be used from command prompt/terminal too.  


![skull stripping](misc/3.jpg?raw=true "Skull Stripping")

## Requirements
1. Supported GPU: NVIDIA DGX 
2. Nvidia Driver 450.80.02
3. CUDA Version: 11.0
4. Python 3.6+
5. Tensorflow, keras
6. Singularity: all the necessary requirements are listed in Singularity recipie file

## User guidance

  
  ### Accessing DeepBrainIPP from web interface:
 -----
     System administrator: Setting up web application
        1. Setup IPP from https://github.com/JaneliaSciComp/jacs-cm"
        2. Setup singularity registry server from https://singularityhub.github.io/sregistry/docs/setup/#pancakes-installation
        3. Build singularity images using the recipe provided in "Singularity" folder
        4. Upload singularity images to installed singularity registry server
        5. Configure pipeline from the admin section
     Users: Accessing web interface and user manual
        1. Use following guideline https://github.com/stjude/DeepBrainIPP/blob/main/misc/DeepBrainIPP_users_manual_github.pdf


### Accessing DeepBrainIPP from command prompt without web interface 

#### Skull Stripping and Paraflocculus Segmentation
-----
        1.  Build singularity images using the recipe provided in "Singularity" folder
            
            sudo singularity build skull_stripping.img skull_stripping_recipie.def
            
        2.  Enter necessary parameters in "config.json" file
        3.  Choose model type in "config.json" that match your MRIs and need less interpolation in resampling 
            invivo-2: 0.06mm X 0.06mm X 0.48mm
            exvivo-1: 0.06mm X 0.06mm X 0.06mm
            exvivo-2: 0.08mm X 0.08mm X 0.08mm
        4.  Run singularity image 
        5.  Make sure your MRIs is a coronal scan (back to front) 
            
            singularity run -B [location of data and absolute path of base folder of DeepBrainIPP] --nv  skull_stripping.img config.json

#### Brain Structure Segmentation
-----
        1.  Build singularity images using the recipe provided in "Singularity" folder
            
            sudo singularity build antsregistrationbatch.img antsregistrationbatch.def
            
        2.  Enter necessary parameters in "registration_config.json" file
        3. Choolse atlas from "Atlas" folder that match you MRIs modality
        4.  Run singularity image 
            
            singularity run -B [location of data and absolute path of base folder of DeepBrainIPP] antsregistrationbatch.img registration_config.json

#### Sub-cerebellar Structure Segmentation
-----
       
        1.  Enter necessary parameters in "registration_config.json" file and make "isCerebellum":"1" 
        2.  Run singularity image 
            
            singularity run -B [location of data and absolute path of base folder of DeepBrainIPP] antsregistrationbatch.img registration_config.json

#### Quantifying Segmented Structures to receive measurements in .csv file
-----
       
        2.  Enter necessary parameters in "registration_config.json" file and "operation_type": "quantifybrain",
            
        5.  Run singularity image 
            
            singularity run -B [location of data and absolute path of base folder of DeepBrainIPP] antsregistrationbatch.img registration_config.json



## Model Training 
  1. Skull Stripping Model
  2. Paraflocculus Model
## Dataset Used for training models:
http://ftp.stjude.org/pub/CBI_Bioimage_Data/DeepBrainIPP_dataset.tgz

## Citation

#### Acknowledgement
We would like to thank Ellis et al. because piece of code has been adapted, updated and customized from thier work titled as "Trialing u-net training modifications for segmenting gliomas using open source deep learning framework"
