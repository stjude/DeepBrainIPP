import ants
from matplotlib.pyplot import figure
import matplotlib.pyplot as plt
import os
import sys

if len(sys.argv) <7:
    print("There is no enough parameters")
    sys.exit() 

def CreateMasks(img_file, startZ, endZ):
    out_file= os.path.dirname(img_file)+'/'+ os.path.splitext( os.path.basename(img_file))[0]+'_mask.nrrd' 
    fixed=ants.image_read(img_file)
    fixed_tmp=fixed
    (w,h,z)=fixed.shape
    
    if (startZ <= z and startZ >=0 and endZ <= z and endZ >=startZ):
        fixed_tmp[:,:,0:startZ]=0.0
        fixed_tmp[:,:,startZ:endZ]=1.0
        fixed_tmp[:,:,endZ:z]=0.0
        ants.image_write(fixed_tmp, out_file)
    else: print("wrong indices to create mask for ", img_file)

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
fixed_file_startZ= int( str(sys.argv[3]).strip())
fixed_file_endZ=int(str(sys.argv[4]).strip())
move_file_startZ=int( str(sys.argv[5]).strip())
move_file_endZ=int(str(sys.argv[6]).strip())

#check file exists or not
checkFileExists(fixed_file)
checkFileExists(move_file)

CreateMasks(fixed_file,fixed_file_startZ,fixed_file_endZ )
CreateMasks(move_file,move_file_startZ,move_file_endZ )

    
