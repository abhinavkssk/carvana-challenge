import cv2
import numpy as np
from matplotlib import pyplot as plt
from PIL import Image
import glob, os

os.chdir('/run/media/abhi/049DF015313ADE78/data/training/')
for file in glob.glob("*GTC.tif"):
	print(file,end='', flush=True)

	img = cv2.imread(file,0)
	thresh1 = cv2.inRange(img,100,150)
	pil_im = Image.fromarray(thresh1)
	full_image_file_noextension=file[:-4]
	print(full_image_file_noextension+"_BW.tif")
	pil_im.save(full_image_file_noextension+"_BW.tif")
