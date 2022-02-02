import nibabel as nib
import csv
import ants
import os
from numpy import double, int
import math
import sys
def CreateLanadMarkImage(img_file, landmark_file,r,c):
    out_file= os.path.dirname(img_file)+'/'+ os.path.splitext( os.path.basename(img_file))[0]+'_landmark.nrrd' 
    print(out_file) 
    img_vol=ants.image_read(img_file)
    #(w,h,z)=img_vol.shape
    img_vol[:,:,:]=0.0
    #read land marks
    with open(landmark_file) as landmaks:
        csv_reader=csv.reader(landmaks,delimiter=',')
        line=0
        lablel=0.0
        for row in csv_reader:
            
            if r is not None and c is not None and (line > r):
                x=math.floor(abs(double(row[c])))
                y=math.floor(abs(double(row[c+1])))
                z=math.floor(abs(double(row[c+2])))
                lablel=lablel+1
                img_vol[x,y,z]=lablel
                print(img_vol[x,y,z])
                
                #print(lablel)
            line=line+1
                
        ants.image_write(img_vol,out_file)   

if len(sys.argv) <7:
    print("There is no enough parameters")
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
fixed_file_landmarks= str(sys.argv[3]).strip()
move_file_landmarks=str(sys.argv[4]).strip()
start_row= int(str(sys.argv[5]).strip())
start_col=int(str(sys.argv[6]).strip())

#check file exists or not
checkFileExists(fixed_file)
checkFileExists(move_file)
checkFileExists(fixed_file_landmarks)
checkFileExists(move_file_landmarks)
    
CreateLanadMarkImage(fixed_file,fixed_file_landmarks,start_row,start_col)
CreateLanadMarkImage(move_file,move_file_landmarks,start_row,start_col)

