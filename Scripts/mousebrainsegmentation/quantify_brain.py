# +
# # +
import numpy, os,sys,glob
from skimage import io
import nibabel as nib
import nrrd
import numpy as np
import subprocess, time
import skimage.measure as measure
import matplotlib.pyplot as plt
import scipy.ndimage.morphology as morphology
import scipy.ndimage as ndimage
import ants
from medpy.io import load, save
import glob, os,sys
import fill_voids

whole_brain_size=0
def execute_command(cmd_to_run, created_file):
    process = subprocess.Popen([cmd_to_run], shell=True, stdout=subprocess.PIPE)
    process.wait()
    #print (process.returncode)
    #process.terminate()
    while True:
        if os.path.exists(created_file):
            break;
        else:
            time.sleep(5)
def modal(arr):
    return stats.mode(arr, axis=None)[0][0]
def measure_whole_brain(reg_cmd,output_path,mask_path,img_moving):
    global whole_brain_size
    output_whole_brain=output_path+"/subregions/whole_brain_mask.nii.gz"
    tmp_cmd= reg_cmd+" -i "+mask_path
    tmp_cmd+=" -o "+ output_whole_brain
    #print(tmp_cmd)
    execute_command(tmp_cmd,output_whole_brain)
    inv_mask,whole_h=load(output_whole_brain)
    org_img=inv_mask.copy()
    inv_mask[img_moving==0]=0
    org_img[img_moving==0]=0
    org_img_med=org_img.copy()
    #print(org_img_med.shape)
    org_img_med=ndimage.filters.median_filter(org_img_med, mode="constant", size=(3,3,1))
    #org_img_med=ndimage.filters.generic_filter(org_img_med, modal, size=(2,3,1))#xyz
    save(org_img,output_path+"/whole_brain_mask.nii.gz", use_compression=False, hdr=whole_h)
    save(org_img_med,output_path+"/whole_brain_mask_med.nii.gz", use_compression=False, hdr=whole_h)
    #org_img=morphology.binary_closing(org_img).astype(np.int32)
    return org_img, org_img_med

def main(path,mask_path,structure_file,resolution,interpolation):
    resolution=resolution[0]*resolution[1]*resolution[2]
    #the transformation matrices 
    tmp_string=""
    file_header=""
    all_measures=open(path+"all_measures.csv",'w')
    for folders in glob.glob(path+"/*"):
        if os.path.isdir(folders): 
            fname=os.path.basename(folders)
            tmp_string=tmp_string+fname+","
            moving_image=glob.glob(folders+"/"+fname+"_segmented_brain.nrrd")
            if len(moving_image)<=0:
                moving_image=glob.glob(folders+"/Cerebellum_extracted.nrrd")
            transformation_file=glob.glob(folders+"/"+"*GenericAffine.mat")
            inverse_transformation=glob.glob(folders+"/"+"*1InverseWarp.nii.gz")
            whole_brain_size=0
            if len(moving_image)>0 and len(transformation_file)>0:
                moving_image=moving_image[0]
                transformation_file=transformation_file[0]
                #inverse transformation file
                
                print(moving_image)

                reg_cmd='''/code/bin/ants/bin/antsApplyTransforms --verbose 1 --dimensionality 3 --float 0 --interpolation '''
                reg_cmd+="NearestNeighbor"
                reg_cmd+=" -r "+moving_image
                reg_cmd+=" -t ["+transformation_file+ ",1]"

                #apply if Syn is used. otherwise comment it
                if inverse_transformation is not None and len(inverse_transformation)>0:
                    inverse_transformation=inverse_transformation[0]
                    reg_cmd+=" -t "+inverse_transformation +" "  

                if(not os.path.exists(folders+"/"+"subregions")):
                    os.makedirs(folders+"/"+"subregions")

                result_files="brain_segmentation_result.csv"
                mask, mask_h=load(mask_path)
                img_moving,mv_h=load(moving_image)
                bit=31
                region_map=[]
                volumes=[]
                volume_suffix=fname
                whole_brain,whole_brain_med=measure_whole_brain(reg_cmd,folders,mask_path,img_moving)
                results=open(folders+"/"+result_files,'w')
                # start applying transformation matrix 
                all_region=np.zeros_like(img_moving)
                with open(structure_file,'r') as regmanp:

                    line=regmanp.readline()
                    file_header=""
                    while line:
                        line=regmanp.readline()
                        print(line)
                        id_name=line.split(",")
                        if (len(id_name)>1):
                            file_header=file_header+","+id_name[1].strip()
                            tmp_mask=np.zeros_like(mask)
                            tmp_mask[mask==int(id_name[0].strip())]=2**15
                            #tmp_mask[mask==int(id_name[0].strip())+32768]=2**15
                            #tmp_mask=clean_maks(tmp_mask)

                            file_name=folders+"/"+"subregions/"+id_name[0].strip()+"_"+id_name[1].strip()+"_"+volume_suffix+"_atlas_mask.nrrd"
                            save(tmp_mask,file_name,hdr=mask_h, use_compression=False)# mask.astype(np.int8))
                            reg_cmd=reg_cmd.replace("NearestNeighbor",interpolation)
                            tmp_cmd= reg_cmd+" -i "+ file_name
                            tmp_cmd+=" -o "+ folders+"/"+"subregions/"+id_name[0].strip()+"_"+id_name[1].strip()+"_mask.nii.gz"
                            #print(tmp_cmd)
                            region_map.append(id_name[1].strip())

                            execute_command(tmp_cmd,folders+"/"+"subregions/"+id_name[0].strip()+"_"+id_name[1].strip()+"_mask.nii.gz")

                            inv_mask,h = load(folders+"/"+"subregions/"+id_name[0].strip()+"_"+id_name[1].strip()+"_mask.nii.gz")
                            threshold=5000
                            if interpolation.strip()=="NearestNeighbor":
                                threshold=25000
                            if "Crus_II" in id_name[1]:
                                threshold=32500
                            if "Crus_I" in id_name[1]:
                                threshold=27000
                            if "Vermis" in id_name[1]:
                                threshold=20000
                            if "PF" in id_name[1]:
                                threshold=800
                            inv_mask[inv_mask>threshold]=2**bit
                            #inv_mask=ndimage.filters.median_filter(inv_mask, mode="constant", size=(3,3,1))
                            inv_mask[inv_mask<2**bit]=0
                            inv_mask[img_moving==0]=0
                            inv_mask=morphology.binary_closing(inv_mask).astype(np.int32)
                            #inv_mask=morphology.binary_fill_holes(inv_mask, structure=np.ones((11,11,11))).astype(np.int32)
                            inv_mask, N = fill_voids.fill(inv_mask, return_fill_count=True)
                            img_moving_tmp=img_moving.copy()
                            all_region[inv_mask==1]=int(id_name[0].strip())
                            img_moving_tmp[inv_mask!=1]=0
                            save(img_moving_tmp,folders+"/"+"subregions/"+id_name[1].strip()+"_extracted.nrrd",hdr=mv_h,use_compression=False)
                            tmp_volume=np.count_nonzero(inv_mask)*resolution
                            #print(id_name[0].strip(),tmp_volume)
                            volumes.append(tmp_volume)

                            save(inv_mask,folders+"/"+"subregions/"+id_name[0].strip()+"_"+id_name[1].strip()+"_mask_med.nii.gz",hdr=mv_h,use_compression=False)

                            #wh_count=np.count_nonzero(whole_brain[whole_brain==int(id_name[0].strip())])
                            wh_count=np.count_nonzero(whole_brain[np.round(whole_brain)==(int(id_name[0].strip()))])
                            wh_count=wh_count*resolution
                            #wh_count_med=np.count_nonzero(whole_brain_med[whole_brain_med==int(id_name[0].strip())])
                            wh_count_med=np.count_nonzero(whole_brain_med[np.round(whole_brain_med)==(int(id_name[0].strip()))])
                            wh_count_med=wh_count_med*resolution
                            whole_brain_size=whole_brain_size+wh_count_med
                            results.write(id_name[1].strip()+","+str(tmp_volume)+","+str(wh_count)+","+str(wh_count_med)+"\n")
                            if "Vermis" in id_name[1]:
                                tmp_string=tmp_string+str(wh_count_med)+","
                            else:
                                tmp_string=tmp_string+str(tmp_volume)+","
                            
                    tmp_string=tmp_string+"\n"
                results.close()   
                save(all_region,folders+"/"+"all_regions.nii.gz")

                plt.figure(figsize=(10,15))
                plt.scatter( np.asarray(volumes), np.asarray(region_map))
                plt.title("Total Brain Size: "+ str(whole_brain_size))
                plt.savefig(folders+"/results.png")
                plt.close()
    all_measures.write(file_header+"\n")
    all_measures.write(tmp_string)            
    all_measures.close()


args=sys.argv
if len(args)<6:
    sys.exit()
else:
    path=args[1].strip()
    if path[len(path)-1] !="/":
        path=path+"/"
    mask_path=args[2].strip()
    structure_file=args[3]
    tmp=args[4].strip().split(",")
    print("resolution",args[4].strip())
    resolution=[float(tmp[0].strip()) ,float(tmp[1].strip()) , float(tmp[2].strip()) ]
    interpolation=args[5].strip()
    

main(path,mask_path,structure_file,resolution,interpolation)


# -


