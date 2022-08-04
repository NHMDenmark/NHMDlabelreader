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


def empty_dataframe():
    record = pd.DataFrame({
        "Alt Cat Number": [],
        "Publish": [],
        "Count": [],
        "Other Remarks": [],
        "Order": [],
        "Family": [],
        "Genus1": [],
        "Species1": [],
        "Determiner First Name": [],
        "Determiner Last Name": [],
        "Determination Remarks": [],
        "Country": [],
        "Locality": [],
        "Start Date": [],
        "Collector First Name": [],
        "Collector Last Name": []
    })
    return record

def parsetext(ocrtext):
    """Parses the transcribed text from a paper card into appropriate data fields.

       ocrtext: A list of lists of strings - one for each line on the paper card.
       Return record: Returns a Pandas data frame with the parsed transcribed data.
    """

    # Skip any beginning blank lines
    line_idx = 0
    for idx in range(0, len(ocrtext)):
        if not ocrtext[idx][0].isspace():
            line_idx = idx
            break

    # Parse first real line
    alt_cat_number = ""
    if ocrtext[line_idx][0].isdigit():
        alt_cat_number = ocrtext[line_idx][0]

    genus = ""
    if len(ocrtext[line_idx]) > 1:
        genus = ocrtext[line_idx][1]

    species = ""
    if len(ocrtext[line_idx]) > 2:
        species = ocrtext[line_idx][2]

    det_remarks = ""
    if len(ocrtext[line_idx]) > 3:
        det_remarks = ''.join(ocrtext[line_idx][3:])

    # TODO: Parse the following lines

    record = pd.DataFrame({
        "Alt Cat Number": [alt_cat_number],
        "Publish": [1],
        "Count": [""],
        "Other Remarks": [""],
        "Order": [""],
        "Family": [""],
        "Genus1": [genus],
        "Species1": [species],
        "Determiner First Name": ["Ole"],
        "Determiner Last Name": ["Bøggild"],
        "Determination Remarks": [det_remarks],
        "Country": [""],
        "Locality": [""],
        "Start Date": [""],
        "Collector First Name": ["Ole"],
        "Collector Last Name": ["Bøggild"]
    })

    return record


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

    segMask = labeldetect.color_segment_labels(img) # Red background
    #segMask = labeldetect.color_segment_labels(img, huerange=(0.5, 0.6)) # Light blue background
    segMask = labeldetect.improve_binary_mask(segMask)
    label_img, num_labels = labeldetect.find_labels(segMask)
    lst_resampled_labels = labeldetect.resample_label(img, label_img, num_labels)

    plt.figure()
    plt.imshow(img)

    plt.figure()
    plt.imshow(label_img)
    print("number of labels detected: " + str(len(lst_resampled_labels)))
    if not len(lst_resampled_labels) == 9:
        print("Warning: Too many detected labels ... terminating program")
        #return  # TODO: Maybe use exit with a non-zero exit code (for later use in shell scripts)


    master_table = empty_dataframe()
    for label_data in lst_resampled_labels:
        print("")
        print("ID " + str(label_data["label_id"]) + " orientation " + str(label_data['orientation']) + " coord " + str(label_data['centroid']))

        img_rgb = img_as_ubyte(label_data['image'])
        ocrreader.read_image(img_rgb)

        ocrtext = ocrreader.get_text()
        for i in range(len(ocrtext)):
            print(ocrtext[i])

        df = parsetext(ocrtext)

        # Add to master table
        master_table = pd.concat([master_table, df], axis=0)

        #ocrreader.visualize_boxes()

        plt.figure()
        plt.imshow(label_data['image'])
        plt.title("ID " + str(label_data["label_id"]))

    plt.show()

    master_table.to_excel("../tests/test.xlsx", index=False)


if __name__ == '__main__':
    main()
