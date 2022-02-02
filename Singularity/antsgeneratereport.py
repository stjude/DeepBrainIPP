import numpy as np
from numpy import double
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from PIL import Image
import time
from matplotlib.pyplot import figure
import PIL
from datetime import datetime
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
import nrrd
import nibabel as nib
import os
import sys
import shutil
import tifffile as tfl
from scipy.ndimage import zoom

if len(sys.argv) <5:
    sys.exit() 


def checkFileExists(file_path):
    exists = os.path.isfile(file_path)
    if exists:
        print("file found at: "+file_path)
    else:
        print(file_path+" file does not exists")
        sys.exit() 
    # Keep presets

#first argument is always the program name 
fixed_file= str(sys.argv[1]).strip()
move_file=str(sys.argv[2]).strip()
output_dir=str(sys.argv[3]).strip()
log_file_name=str(sys.argv[4]).strip()
reg_file=str(sys.argv[5]).strip()
run_cmd=str(sys.argv[6]).strip()

#check file exists or not
checkFileExists(log_file_name)
checkFileExists(reg_file)

#DIAGNOSTIC,Iteration,metricValue,convergenceValue,ITERATION_TIME_INDEX,SINCE_LAST
line_indices=[]
stage_indices=[]
vol_size=[]
elapsed_time=[]

for n,line in enumerate(open(log_file_name)):
    if "DIAGNOSTIC,Iteration,metricValue,convergenceValue,ITERATION_TIME_INDEX,SINCE_LAST" in line:
        line_indices.append((n+1))
    if "*** Running " in line:
        stage_indices.append((n+1))
    if "Size: [" in line:
        vol_size.append((n+1))
    if "Elapsed time (stage " in line:
        elapsed_time.append((n+1))
#print(line_indices)
#print(stage_indices)
#print(vol_size)
#print(elapsed_time)





tolat_leve=0
def getLinesAndReport(startind, endindex,fl,filename,level,stage_name ,volume_size_sp):
    iteration=[]
    metricValue=[]
    convergenceValue=[]
    SINCE_LAST=[]
    total_voxels= int(volume_size_sp[0])*int(volume_size_sp[1])*int(volume_size_sp[1])
    while (startind<endindex-1):
        line_split=fl[startind].split(",")
        iteration.append(int(line_split[1].strip()))
        metricValue.append(round( np.abs(double(line_split[2].strip())),4))
        convergenceValue.append(round( double(line_split[3].strip()),4))
        SINCE_LAST.append(double(line_split[5].strip()))
        startind=startind+1
        if("Elapsed time" in fl[startind]):
            break
    #print(iteration)
    iteration=np.asarray(iteration)
    metricValue=np.asarray(metricValue)
    avg_metricValue=np.average(metricValue)
    #2/(sqrt(n)-|K|)
    significance=2/(np.sqrt(total_voxels)-(int(volume_size_sp[0])+int(volume_size_sp[1])+int(volume_size_sp[1])))
    sig_message=""
    if (avg_metricValue>significance):
        sig_message="outcome is statistically significant"
        red_patch = mpatches.Patch(color='g', label=sig_message)
    else:
        sig_message="outcome is not statistically significant"
        red_patch = mpatches.Patch(color='red', label=sig_message)
    #print(sig_message)
    convergenceValue=np.asarray(convergenceValue)
    #print(avg_metricValue,significance)
    SINCE_LAST=np.around(SINCE_LAST, decimals=5)
    SINCE_LAST=np.asarray(SINCE_LAST)
    plt.figure(level)
    plt.subplot(211)
    plt.ylabel('Metric value')
    plt.legend(handles=[red_patch])
    plt.title(stage_name+' Level:' +str(level)+" ")
    plt.plot(iteration, metricValue, 'r')
    plt.subplot(212)
    plt.ylabel('Convergence value')
    plt.plot(iteration,convergenceValue, 'b')
    #plt.subplot(313)
    #plt.ylabel('Update since last')
    #plt.plot(iteration, SINCE_LAST, 'g')
    plt.xlabel('Iteration')
    plt.savefig(filename)
    #plt.show()   

def getStages(index,fl):   
    line=fl[index-1]
    line=line.replace("*** Running","")
    line=line.replace("***","")
    line=line.replace("\n","")
    line=line.strip()
    line=line.split(" ")[0]
    return line
def getVolume(index,fl):
    line=fl[index-1]
    line=line.replace("Size: [","")
    line=line.replace("]","")
    return line
def gettimeElapsed(index,fl):
    line=fl[index-1]
    line=line.split(":")
    return line[1]        

last_indx=0
with open(log_file_name) as f:
    time_pre=time.time()
    del_dir=output_dir+str(time_pre)
    os.mkdir(output_dir+str(time_pre))
    
    alldata=f.readlines()
    prefix_filename=output_dir+str(time_pre)+"/regsummaryreport"
    filenames=[]
    stage_indx=0;
    stage_name=""
    volume_size=getVolume(vol_size[0],alldata)
    volume_size_sp=volume_size.split(",")
    
    #print(volume_size)
    for indx in range(len(line_indices)-1):#iterating through all level block
        last_indx=indx
        #print("between :",line_indices[indx],line_indices[indx+1])
        time_pre=time.time()
        filename=prefix_filename+"_"+str(indx)+"_"+str(time_pre)+".png"
        filenames.append(filename)
        if(stage_indx <len(stage_indices) and line_indices[indx]>stage_indices[stage_indx]):
            stage_name=getStages(stage_indices[stage_indx], alldata)#adding stage name 
            stage_indx=stage_indx+1
        getLinesAndReport(line_indices[indx],line_indices[indx+1],alldata,filename,indx, stage_name,volume_size_sp)
    last_indx=last_indx+1
    time_pre=time.time()
    filename=prefix_filename+"_"+str(last_indx)+"_"+str(time_pre)+".png"
    filenames.append(filename)
    getLinesAndReport(line_indices[last_indx],len(alldata),alldata,filename, last_indx,stage_name,volume_size_sp)   
    tolat_level=len(line_indices)
    
   

    fixed=fixed_file
    movable=move_file
    summary_file=""
    for indx in stage_indices:
        stg=getStages(indx,alldata)
        stg=str(stg).replace("registration", "")
        summary_file=summary_file+stg+"_"
    time_seq=str(round(time.time()))
    pp = PdfPages(output_dir+summary_file+'_'+time_seq+'.pdf')
    print("Generatng reports for " +summary_file +" transformation ")
    #Elapsed Time
    el_time_str=""
    stg_indx=1
    total_time=0
    for t in elapsed_time:
        stage_time=round(double(gettimeElapsed(t,alldata).strip())/60)
        total_time=total_time+stage_time
        el_time_str=el_time_str+ " stage#"+str(stg_indx)+": "+str(stage_time) +" min, "
        stg_indx=stg_indx+1
    el_time_str=el_time_str+" Total: "+ str(total_time)+" min"
    
    
    now = datetime.now()
    dt_string = now.strftime("%m/%d/%Y %H:%M:%S")
    last_indx=last_indx+1
    plt.figure(last_indx)
    
    def_page_size=11
    page_sige=int(30*tolat_level/8)
    if page_sige<def_page_size:
        page_sige=def_page_size
    
    
    fig=plt.figure(figsize=(17, page_sige))
    fig.suptitle("Ants Registration Summary\n Date:"+str(dt_string)+"\n\n Volumes\n Fixed: "+fixed+"\n Move: "+movable +"\n volume size: "+volume_size+"\n Elapsed time: "+el_time_str ,fontsize=12)
    idx=1
    for flname in filenames:
        i = idx % 4 # Get subplot row
        j = idx // 2 # Get subplot column
        image = Image.open(flname)
        fig.add_subplot(int(tolat_level/2), 2, idx),plt.imshow(image)
        plt.axis('off')
        idx=idx+1
    plt.subplots_adjust(wspace=0, hspace=0)
    plt.savefig("Registration_summary.png")
    pp.savefig(fig)
    plt.close()
    
    
    #Qualitative evaluations 
    #Slice from fixed file
    last_indx=last_indx+1
    fn,ext=os.path.splitext(fixed_file)
    raw_data_fixed=None
    raw_data_move=None
    if(ext==".nrrd"):
        raw_data_fixed, header=nrrd.read(fixed_file)
    elif(ext==".tif"):
        raw_data_fixed=tfl.imread(fixed_file)
    
    fn,ext=os.path.splitext(move_file)
    if(ext==".nrrd"):
        raw_data_move, header=nrrd.read(move_file)
    elif(ext==".tif"):
        raw_data_move=tfl.imread(move_file)
    print(raw_data_fixed.shape, raw_data_move.shape)
    if (len( raw_data_move.shape)>3):
        raw_data_move=raw_data_move[0,:,:,:]
    #adjust size input and output volume
    if(raw_data_fixed.shape[2] !=raw_data_move.shape[2]): 
        raw_data_move = zoom(raw_data_move, (1, 1, raw_data_fixed.shape[2]/raw_data_move.shape[2]))
        
    reg_data_read=nib.load(reg_file)
    reg_data_reg = reg_data_read.get_fdata()   
        
    #print(raw_data_fixed.shape)
    
    fig22=plt.figure(figsize=(17, 11))
    fig22.suptitle("Subjective Evaluations" ,fontsize=20)
    #raw data
    #slice from fixed file
    slic_fixed=raw_data_fixed[:,:,int(raw_data_fixed.shape[2]/2)]
    fig22.add_subplot(1, 2, 1),plt.imshow(slic_fixed,'gray', interpolation='none')
    plt.title('Fixed data')
    plt.axis('off')
    #slice from move file
    
    #print(raw_data_move.shape)
    slic1_move=raw_data_move[:,:,int(raw_data_move.shape[2]/2)]
    fig22.add_subplot(1, 2, 2),plt.imshow(slic1_move,'gray', interpolation='none', alpha=0.5)
    plt.axis('off')
    plt.title('Movable')
    
    fig22.suptitle("Raw volume")
    pp.savefig(fig22)
    plt.close()
   
    
    #XY slice
    #slice from fixed file
    fig2=plt.figure(figsize=(17, 11))
    slic_fixed=raw_data_fixed[:,:,int(raw_data_fixed.shape[2]/2)]
    fig2.add_subplot(1, 3, 1),plt.imshow(slic_fixed,'gray', interpolation='none')
    plt.title('slice Z# '+str(int(raw_data_fixed.shape[2]/2))+' Plane-XY')
    plt.axis('off')
    #slice from move file
    
    #print(raw_data_move.shape)
    slic1_move=raw_data_move[:,:,int(raw_data_move.shape[2]/2)]
    fig2.add_subplot(1, 3, 1),plt.imshow(slic1_move,'jet', interpolation='none', alpha=0.5)
    plt.axis('off')
    fig2.suptitle("Composite before registration")
    
    #YZ
    #slice from fixed file
    slic_fixed=raw_data_fixed[int(raw_data_fixed.shape[0]/2),:,:]
    fig2.add_subplot(1, 3, 2),plt.imshow(slic_fixed,'gray', interpolation='none')
    plt.title('slice X# '+str(int(raw_data_fixed.shape[0]/2))+' Plane-YZ')
    plt.axis('off')
    #slice from move file
    #print(raw_data_move.shape)
    slic1_move=raw_data_move[int(raw_data_move.shape[0]/2),:,:]
    fig2.add_subplot(1, 3, 2),plt.imshow(slic1_move,'jet', interpolation='none', alpha=0.5)
    plt.axis('off')
    
    #ZX
    #slice from fixed file
    slic_fixed=raw_data_fixed[:,int(raw_data_fixed.shape[1]/2),:]
    fig2.add_subplot(1, 3, 3),plt.imshow(slic_fixed,'gray', interpolation='none')
    plt.title('slice Y# '+str(int(raw_data_fixed.shape[1]/2))+' Plane-ZX')
    plt.axis('off')
    #slice from move file
    #print(raw_data_move.shape)
    slic1_move=raw_data_move[:,int(raw_data_move.shape[1]/2),:]
    fig2.add_subplot(1, 3, 3),plt.imshow(slic1_move,'jet', interpolation='none', alpha=0.5)
    plt.axis('off')
   
    #plt.show()
    pp.savefig(fig2)
    plt.close()
    
    #slice from registered file
    last_indx=last_indx+1
   
    
    #XY slice
    #slice from fixed file
    fig3= plt.figure(figsize=(17, 11))
    slic_fixed=raw_data_fixed[:,:,int(raw_data_fixed.shape[2]/2)]
    fig3.add_subplot(1, 3, 1),plt.imshow(slic_fixed,'gray', interpolation='none')
    plt.title('slice Z# '+str(int(raw_data_fixed.shape[2]/2))+' Plane-XY')
    plt.axis('off')
    #slice from move file

    slic1_move=reg_data_reg[:,:,int(reg_data_reg.shape[2]/2)]
    fig3.add_subplot(1, 3, 1),plt.imshow(slic1_move,'jet', interpolation='none', alpha=0.5)
    plt.axis('off')
    fig3.suptitle("Composite after registration")
    
    #YZ
    #slice from fixed file
    slic_fixed=raw_data_fixed[int(raw_data_fixed.shape[0]/2),:,:]
    fig3.add_subplot(1, 3, 2),plt.imshow(slic_fixed,'gray', interpolation='none')
    plt.title('slice X# '+str(int(raw_data_fixed.shape[0]/2))+' Plane-YZ')
    plt.axis('off')
    #slice from move file
    #print(reg_data_reg.shape)
    slic1_move=reg_data_reg[int(reg_data_reg.shape[0]/2),:,:]
    fig3.add_subplot(1, 3, 2),plt.imshow(slic1_move,'jet', interpolation='none', alpha=0.5)
    plt.axis('off')
    
    #ZX
    #slice from fixed file
    slic_fixed=raw_data_fixed[:,int(raw_data_fixed.shape[1]/2),:]
    fig3.add_subplot(1, 3, 3),plt.imshow(slic_fixed,'gray', interpolation='none')
    plt.title('slice Y# '+str(int(raw_data_fixed.shape[1]/2))+' Plane-ZX')
    plt.axis('off')
    #slice from move file
    #print(reg_data_reg.shape)
    slic1_move=reg_data_reg[:,int(reg_data_reg.shape[1]/2),:]
    fig3.add_subplot(1, 3, 3),plt.imshow(slic1_move,'jet', interpolation='none', alpha=0.5)
    plt.axis('off')
    
    ch_cnt=0
    while (ch_cnt <len(str(run_cmd))):
        if(ch_cnt%200==0):
            run_cmd=run_cmd[:ch_cnt] + '\n' + run_cmd[ch_cnt:]
        ch_cnt=ch_cnt+1
    plt.figtext(0.08, 0.05, run_cmd, horizontalalignment='left')
    
    #plt.show()
    pp.savefig(fig3)
    plt.close()
    pp.close()
    #delete temp folder created to process graph
    shutil.rmtree(del_dir)
    f.close()
    f_path, f_name=os.path.split(reg_file)
    
    os.rename(reg_file,f_path+'/'+summary_file+'_'+time_seq+'.nii.gz')

    
        
        
        

