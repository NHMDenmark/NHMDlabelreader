# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 19:18:00 2022

@author: Kim Steenstrup Pedersen, NHMD

Copyright (c) 2022  Natural History Museum of Denmark (NHMD)

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

import argparse
from skimage.io import imread, imsave
import matplotlib.pyplot as plt
import pandas as pd
import re
from pathlib import PurePath, Path
from wand.image import Image
import numpy as np


from labelreader.ocr import tesseract
from labelreader.util.util import checkfilepath


def empty_dataframe():
    record = pd.DataFrame({
        "Sub-Order": [],
        "Family": [],
        "Sub-Family": [],
        "Super-Genus": [],
        "Genus": [],
        "Species": []
    })
    return record


def isSpeciesName(text):
    """Return true if text has the format of a species name.

            text: String to analyse
            Return: Boolean
        """
    if re.match('^—(\w|\s|\d|[().,])+', text):
        return True
    else:
        return False



def parsetable(ocrtext, taxon_tree):
    # TOOD: Parse table content

    df = empty_dataframe()
    lastLineSpecies = False

    # Loop over lines in ocrtext
    for line in ocrtext:
        linetext = ' '.join(line)
        if isSpeciesName(linetext):
            # print("Species: " + linetext)
            lastLineSpecies = True
            species = ' '.join(line[1:4]) # TODO: Does this always work? No - to fix
            #  If isSpeciesName then reuse fields from taxon_tree, but check if exists
            #  Else reset taxon_tree = dict() and read other fields in order

            level1 = ""
            if "Sub-Order" in taxon_tree:
                level1 = taxon_tree["Sub-Order"]

            level2 = ""
            if "Family" in taxon_tree:
                level2 = taxon_tree["Family"]

            level3 = ""
            if "Sub-Family" in taxon_tree:
                level3 = taxon_tree["Sub-Family"]

            level4 = ""
            if "Super-Genus" in taxon_tree:
                level4 = taxon_tree["Super-Genus"]

            level5 = ""
            if "Genus" in taxon_tree:
                level5 = taxon_tree["Genus"]

            record = pd.DataFrame({
                        "Sub-Order": [level1],
                        "Family": [level2],
                        "Sub-Family": [level3],
                        "Super-Genus": [level4],
                        "Genus": [level5],
                        "Species": [species]
            })
            df = pd.concat([df, record], axis=0, ignore_index=True)
        else:
            if lastLineSpecies:
                taxon_tree = dict()

            if "Sub-Order" in taxon_tree:
                if "Family" in taxon_tree:
                    if "Sub-Family" in taxon_tree:
                        if "Super-Genus" in taxon_tree:
                            if not ("Genus" in taxon_tree):
                                taxon_tree["Genus"] = linetext
                        else:
                            taxon_tree["Super-Genus"] = linetext
                    else:
                        taxon_tree["Sub-Family"] = linetext
                else:
                    taxon_tree["Family"] = linetext
            else:
                taxon_tree["Sub-Order"] = linetext

    return df, taxon_tree

def process_image(img, imgfilename, no_img, no_pages, args, ocrreader, master_table, taxon_tree):
    """Parse one image and create a row in the master_table"""
    if args["verbose"]:
        plt.figure()
        plt.imshow(img)

    # Remove right half of the image
    (_, width, _) = img.shape

    if no_pages % 2 == 0: #  Even pages
        #imghalf = img[900:10800, 500:int(width * 0.52)]
        imghalf = img[500:5400, 300:int(width * 0.52), :]
    else: #  Odd pages
        #imghalf = img[900:10800, 0:int(width*0.45)]
        imghalf = img[500:5400, 0:int(width * 0.45), :]

    if args["verbose"]:
        plt.figure()
        plt.imshow(imghalf)

    ocrreader.read_image(imghalf)

    ocrtext = ocrreader.get_text()

    if args["verbose"]:
        for i in range(len(ocrtext)):
            print(ocrtext[i])

    df, taxon_tree = parsetable(ocrtext, taxon_tree)

    # Add to master table
    master_table = pd.concat([master_table, df], axis=0, ignore_index=True)

    return master_table, taxon_tree



def main():
    """The main function of this script."""
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser(description="Transcribe Butterfly atlas taxon table from consecutive images.")
    ap.add_argument("-t", "--tesseract", required=True,
                    help="path to tesseract executable")
    ap.add_argument("-i", "--image", required=True, action="extend", nargs="+", type=str,
                    help="file name for and path to input image")
    ap.add_argument("-o", "--output", required=False, default="../output",
                    help="path and filename for Excel spreadsheet to write result to.")
    ap.add_argument("-l", "--language", required=False, default="dan+eng",
                    help="language that tesseract uses - depends on installed tesseract language packages")
    ap.add_argument("-r", "--resolution", required=False, default=600, type=int,
                    help="Set resolution in DPI of scanned images - used for rendering pdf pages so only relevant for PDF files")
    ap.add_argument("-v", "--verbose", required=False, action='store_true', default=False,
                    help="If set the program is verbose and will print out debug information")

    args = vars(ap.parse_args())


    print("Using language = " + args["language"] + "\n")

    # Initialize the OCR reader object
    ocrreader = tesseract.OCR(args["tesseract"], args["language"], config='--psm 6 -c preserve_interword_spaces=1 --dpi ' + str(args["resolution"]))

    master_table = empty_dataframe()
    taxon_tree = dict() # Initialize with an empty dictionary

    # Loop over a directory of images
    no_img = 0  # Count number of images
    for imgfilename in args["image"]:
        print("Transcribing " + imgfilename)
        no_img += 1
        # Check if it is a pdf file
        if Path(imgfilename).suffix == '.pdf':
            print("Reading pages in a pdf file")
            with Image(filename=imgfilename, resolution=args["resolution"]) as img_wand_all:
                no_pages = 0
                # Read all pages
                for img_wand in img_wand_all.sequence:
                    img = np.array(img_wand)
                    no_pages += 1
                    master_table, taxon_tree = process_image(img, imgfilename, no_img, no_pages, args, ocrreader, master_table, taxon_tree)
        elif Path(imgfilename).suffix == '.tif':
            no_pages = int(imgfilename.split('_')[3])
            # Read image file
            img = imread(imgfilename, plugin='pil')
            master_table, taxon_tree = process_image(img, imgfilename, no_img, no_pages, args, ocrreader, master_table, taxon_tree)
        else:
            no_pages = int(imgfilename.split('_')[3])
            # Read image file
            img = imread(imgfilename)
            master_table, taxon_tree = process_image(img, imgfilename, no_img, no_pages, args, ocrreader, master_table, taxon_tree)


    # Write Excel sheet to disk
    master_table.to_excel(PurePath(args["output"], "table.xlsx").as_posix(), index=False)

    # If verbose mode then show all opened figures
    if args["verbose"]:
        plt.show()


if __name__ == '__main__':
    main()
