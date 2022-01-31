# DeepBrainIPP: An end-to-end pipeline for automated mouse brain structures segmentation and morphology analysis.

# Background
DeepBrainIpp is a pipeline for skull stripping, brain structures segmentation and morphogenetic characterization. People with/without technical expertise can use DeepBrainIPP. For Non-computational research staff a system administrator can setup four components (Web Application, Job Manager, Singularity Repository, Computing Node) of DeepBrainIPP to access it via web browser. However, DeepBrainIPP can be used from command prompt/terminal too.  


![skull stripping](misc/3.jpg?raw=true "Skull Stripping")

# User guidance
  
  Using DeepBrainIPP from web interface:<br/><br/>
    Setting up web application (for System administrator):<br/>
        1. Setup IPP from https://github.com/JaneliaSciComp/jacs-cm <br/>
        2. Setup singularity registry server from https://singularityhub.github.io/sregistry/docs/setup/#pancakes-installation <br/>
        3. Build singularity images using the recipe provided in "singularity_recipie" folder <br/>
        4. Upload singularity images to installed singularity registry server <br/>
        5. Configure pipeline from the admin section <br/>
  Accessing web interface and user manual (for users): <br/>
        1. Use following guideline https://github.com/stjude/DeepBrainIPP/blob/main/misc/DeepBrainIPP_users_manual_github.pdf

<br/> 
Using DeepBrainIPP from command prompt without web interface 

# Model Training 
  1. Skull Stripping Model
  2. Paraflocculus Model


# Citation
