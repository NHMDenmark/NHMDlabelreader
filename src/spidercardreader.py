# -*- coding: utf-8 -*-
"""
Created on Thu May 26 17:44:00 2022

@author: Kim Steenstrup Pedersen, NHMD

Copyright 2022 Natural History Museum of Denmark (NHMD)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software 
distributed under the License is distributed on an "AS IS" BASIS, 
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. 
See the License for the specific language governing permissions and 
limitations under the License. 
"""

# import sys
import argparse
from skimage.io import imread
from skimage.util import img_as_ubyte
import matplotlib.pyplot as plt
import pandas as pd

# Adding path to ocr package - this can probably be done smarter
# from pathlib import Path
# print("Adding to syspath: " + str(Path(__file__).parent.parent))
# sys.path.append(str(Path(__file__).parent.parent))

from labelreader.ocr import tesseract
from labelreader.labeldetect import labeldetect


def main():
    """The main function of this script."""
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--tesseract", required=True,
                    help="path to tesseract executable")
    ap.add_argument("-i", "--image", required=True,
                    help="file name for and path to input image")
    ap.add_argument("-l", "--language", required=False, default="dan+eng",
                    help="language that tesseract uses - depends on installed tesseract language packages")
    args = vars(ap.parse_args())

    print("Using language = " + args["language"] + "\n")

    # Initialize the OCR reader object
    ocrreader = tesseract.OCR(args["tesseract"], args["language"])

    # Read image with filename args["image"]
    img = imread(args["image"])

    segMask = labeldetect.color_segment_labels(img)
    segMask = labeldetect.improve_binary_mask(segMask)
    label_img, num_labels = labeldetect.find_labels(segMask)
    lst_resampled_labels = labeldetect.resample_label(img, label_img, num_labels)

    plt.figure()
    plt.imshow(label_img)
    print("number of labels detected: " + str(num_labels))

    for label_data in lst_resampled_labels:
        print("")
        print("ID " + str(label_data["label_id"]) + " orientation " + str(label_data['orientation']) + " coord " + str(label_data['centroid']))

        img_rgb = img_as_ubyte(label_data['image'])
        ocrreader.read_image(img_rgb)

        ocrtext = ocrreader.get_text()
        for i in range(len(ocrtext)):
            print(ocrtext[i])

        #ocrreader.visualize_boxes()

        plt.figure()
        plt.imshow(label_data['image'])
        plt.title("ID " + str(label_data["label_id"]))

    plt.show()


if __name__ == '__main__':
    main()
