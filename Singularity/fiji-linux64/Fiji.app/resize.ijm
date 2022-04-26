args = getArgument()
print(args)
args = split(args, "##");

file_path=args[0]
filename=args[1]
isEnhance=args[2]
//run("Bio-Formats Importer", "open="+fixed_file+" autoscale color_mode=Default rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT");
run("Image Sequence...", "open="+file_path+" scale=100 file="+filename); 
if(isEnhance=="True"){
	run("Enhance Contrast...", "saturated=0.3 process_all");
	print("finish contast enhancement");
}

run("Properties...", "unit=microns pixel_width=1.0000 pixel_height=1.0000 voxel_depth=1.0000");
run("Nrrd ... ", "nrrd="+file_path+"modified_"+filename);
close();
