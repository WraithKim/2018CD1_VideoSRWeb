from PIL import Image,ImageFilter
import os, os.path
import numpy as np
import sys
import time




def aug_image(img,aug):

    if aug=="blur":
        return img.filter(ImageFilter.BLUR)

    elif aug == "edge_enhance":

        return img.filter(ImageFilter.EDGE_ENHANCE)

    return img


def aug_all_folder(input,output,command):
    valid_images = [".jpg", ".gif", ".png", ".tga",".jpeg"]

    for f in os.listdir(input):
        print("_----------------------_")
        print(f)
        time.sleep(1)
        ext = os.path.splitext(f)[1]
        if ext.lower() not in valid_images:
            continue
        img = Image.open(input+f)
        aug_image(img,command).save(output+f)



if __name__ =="__main__":

    imgs = []
    valid_images = [".jpg", ".gif", ".png", ".tga",".jpeg"]
    dirpath = sys.argv[1]
    outputpath = sys.argv[2]
    command = sys.argv[3]

    for f in os.listdir(dirpath):
        print(f)
        ext = os.path.splitext(f)[1]
        if ext.lower() not in valid_images:
            continue
        img = Image.open(dirpath+f)
        aug_image(img,command).save(outputpath+f)











