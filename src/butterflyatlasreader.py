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
from skimage.io import imread
import matplotlib.pyplot as plt
import pandas as pd
import re
from pathlib import PurePath, Path
from wand.image import Image
import numpy as np

from labelreader.ocr import tesseract
#from labelreader.util.util import checkfilepath


def empty_dataframe():
    record = pd.DataFrame({
        "Sub-Order": [],
        "Super-Family": [],
        "Family": [],
        "Sub-Family": [],
        "Genus": [],
        "Species": []
    })
    return record


def cleanPrefix(text):
    """Removes prefixed whitespace, digits, and dashes.

        text: String to analyse
        Return: Clean string
    """
    return re.sub('^(\d|\s)*([‚]|—|-)+\s*', '', text)

def cleanPostfix(text):
    """Removes postfixed whitespace, stars, and dots.

        text: String to analyse
        Return: Clean string
    """
    return re.sub('\s*([.*]|\d|[a-z])+$', '', text)

def isFamilyAuthorName(text):
    """Return true if text has the format of an author name.

        text: String to analyse
        Return: Boolean
    """
    if re.match('^[(](\w|\s|[&,])+[,]{0,1}(\d|\s)*[)]', text):
        return True
    else:
        return False


def isGenusAuthorName(text):
    """Return true if text has the format of a genus author name.

        text: String to analyse
        Return: Boolean
    """
    if re.match('^[(]?(\w|\s|[&,])+[,]{0,1}(\d|\s)*[)]?', text):
        return True
    else:
        return False

def isSpeciesName(text):
    """Return true if text has the format of a species name.

        text: String to analyse
        Return: Boolean
    """
    # NOTE: Added capital letters to counter OCR errors
    if re.match('^(\d|\s)*(—|-|[‚.])+\s+([A-Za-zæøåüı10»«\]]|—|-)*(\w|\s|\d|[(),])+', text):
        return True
    else:
        return False


def isGenusName(text):
    """Return true if text has the format of a genus name.

            text: String to analyse
            Return: Boolean
        """
    if re.match('^[A-Zı]+(\w|\s|\d|[ı(),])+', text):
        return True
    else:
        return False

def isSubFamilyName(text):
    """Return true if text has the format of a super-genus name.

        text: String to analyse
        Return: Boolean
    """
    if re.match('^[A-Z]\w+inae', text):
        return True
    else:
        return False

def isFamilyName(text):
    """Return true if text has the format of a sub-family name.

        text: String to analyse
        Return: Boolean
    """
    # NOTE: Added capital letters to counter OCR errors
    if re.match('^[A-Z]+(IDAE|HDAE)[ ]*[(]{0,1}(\w|\s)*[)]{0,1}[ ]{0,1}[.]*', text):
        return True
    else:
        return False


def isSuperFamilyName(text):
    """Return true if text has the format of a family name.

        text: String to analyse
        Return: Boolean
    """
    # NOTE: Added capital letters to counter OCR errors
    if re.match('^([A-Z]|\s)+(IDEA|HDEA)', text):
        return True
    else:
        return False

def isSubOrder(text):
    """Return true if text has the format of a sub-order name.

            text: String to analyse
            Return: Boolean
        """
    if re.match('^([A-Z-—]|\s)+A', text) and not isSuperFamilyName(text):
        return True
    else:
        return False


class TaxonTreeParser():
    """Representation of the taxon parse tree to be used by the parser.
       Internally the tree is a dictionary containing the taxonomic levels and currently read values
    """
    def __init__(self):
        """Initialize internal data structure"""
        self.taxon_tree_dict = dict()
        self.previousLineWasSpecies = False
        self.previousLineWasGenus = False
        self.previousLineWasFamily = False

    def parsetable(self, ocrtext):
        """Parse table content

            ocrtext: list of lists of strings to be parsed
            Return df, taxon_tree: A Pandas dataframe with parsed data and the current taxon_tree dictionary containing
                                   the state of the parser.
        """
        df = empty_dataframe()

        # Loop over lines in ocrtext
        for line in ocrtext:
            linetext = ' '.join(line)
            if isSpeciesName(linetext):
                # print("Species: " + linetext)
                self.previousLineWasSpecies = True

                # Strip species name of leading and trailing characters
                species = cleanPostfix(cleanPrefix(' '.join(line)))

                #  If isSpeciesName then reuse fields from taxon_tree, but check if exists
                level1 = ""
                if "Sub-Order" in self.taxon_tree_dict:
                    level1 = self.taxon_tree_dict["Sub-Order"]

                level2 = ""
                if "Super-Family" in self.taxon_tree_dict:
                    level2 = self.taxon_tree_dict["Super-Family"]

                level3 = ""
                if "Family" in self.taxon_tree_dict:
                    level3 = self.taxon_tree_dict["Family"]

                level4 = ""
                if "Sub-Family" in self.taxon_tree_dict:
                    level4 = self.taxon_tree_dict["Sub-Family"]

                level5 = ""
                if "Genus" in self.taxon_tree_dict:
                    level5 = self.taxon_tree_dict["Genus"]

                record = pd.DataFrame({
                            "Sub-Order": [level1],
                            "Super-Family": [level2],
                            "Family": [level3],
                            "Sub-Family": [level4],
                            "Genus": [level5],
                            "Species": [species]
                })
                df = pd.concat([df, record], axis=0, ignore_index=True)
            else:
                #  Else reset taxon_tree = dict() and read other fields in order

                # Reset taxon_tree dictionary
                if self.previousLineWasSpecies:
                    self.previousLineWasSpecies = False
                    if "Genus" in self.taxon_tree_dict:
                        self.taxon_tree_dict.pop("Genus")
                    if isSubFamilyName(linetext) and ("Sub-Family" in self.taxon_tree_dict):
                        self.taxon_tree_dict.pop("Sub-Family")
                    elif isFamilyName(linetext) and ("Family" in self.taxon_tree_dict):
                        if "Sub-Family" in self.taxon_tree_dict:
                            self.taxon_tree_dict.pop("Sub-Family")
                        self.taxon_tree_dict.pop("Family")
                    elif isSuperFamilyName(linetext) and ("Super-Family" in self.taxon_tree_dict):
                        if "Sub-Family" in self.taxon_tree_dict:
                            self.taxon_tree_dict.pop("Sub-Family")
                        if "Family" in self.taxon_tree_dict:
                            self.taxon_tree_dict.pop("Family")
                        self.taxon_tree_dict.pop("Super-Family")
                    elif isSubOrder(linetext) and ("Sub-Order" in self.taxon_tree_dict):
                        self.taxon_tree_dict = dict()

                # Add next line to appropriate field
                readingDoubleLineFamilyName = False
                if self.previousLineWasFamily: # Handle 2-lines Family names
                    self.previousLineWasFamily = False
                    if isFamilyAuthorName(linetext) and ("Family" in self.taxon_tree_dict):
                        self.taxon_tree_dict["Family"] = self.taxon_tree_dict["Family"] + " " + linetext
                        readingDoubleLineFamilyName = True
                    else:
                        readingDoubleLineFamilyName = False

                readingDoubleLineGenusName = False
                if self.previousLineWasGenus: # Handle 2-lines Family names
                    self.previousLineWasGenus = False
                    if isGenusAuthorName(linetext) and ("Genus" in self.taxon_tree_dict):
                        self.taxon_tree_dict["Genus"] = self.taxon_tree_dict["Genus"] + " " + linetext
                        readingDoubleLineGenusName = True
                    else:
                        readingDoubleLineGenusName = False

                if isSuperFamilyName(linetext) and not ("Super-Family" in self.taxon_tree_dict):
                    self.taxon_tree_dict["Super-Family"] = re.sub('\s', '', linetext)

                elif isSubOrder(linetext) and not ("Sub-Order" in self.taxon_tree_dict):
                    # Important that this comes after Super-Family due to name checker
                    self.taxon_tree_dict["Sub-Order"] = linetext

                elif isFamilyName(linetext) and not ("Family" in self.taxon_tree_dict):
                    self.taxon_tree_dict["Family"] = cleanPostfix(linetext)
                    self.previousLineWasFamily = True

                elif isSubFamilyName(linetext) and not ("Sub-Family" in self.taxon_tree_dict):
                    self.taxon_tree_dict["Sub-Family"] = linetext

                elif isGenusName(linetext) and not ("Genus" in self.taxon_tree_dict):
                    self.taxon_tree_dict["Genus"] = linetext
                    self.previousLineWasGenus = True

                else:
                    if not (readingDoubleLineFamilyName or readingDoubleLineGenusName):
                        print("Line not processed = '" + linetext + "'")

        return df




def process_image(img, no_pages, args, ocrreader, master_table, taxon_tree):
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
        imghalf = img[500:5400, 0:int(width * 0.44), :]

    if args["verbose"]:
        plt.figure()
        plt.imshow(imghalf)

    ocrreader.read_image(imghalf)

    ocrtext = ocrreader.get_text()

    if args["verbose"]:
        for i in range(len(ocrtext)):
            print(ocrtext[i])

    df = taxon_tree.parsetable(ocrtext)

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
    ap.add_argument("-o", "--output", required=False, default="../output/output.xlsx",
                    help="path and filename for Excel spreadsheet to write result to.")
    ap.add_argument("-l", "--language", required=False, default="deu",
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
    #taxon_tree = dict() # Initialize with an empty dictionary representing the taxon tree
    taxon_tree = TaxonTreeParser()

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
                    print("Processing page " + str(no_pages))
                    master_table, taxon_tree = process_image(img, no_pages, args, ocrreader, master_table, taxon_tree)
        elif Path(imgfilename).suffix == '.tif':
            no_pages = int(imgfilename.split('_')[3])
            # Read image file
            img = imread(imgfilename, plugin='pil')
            master_table, taxon_tree = process_image(img, no_pages, args, ocrreader, master_table, taxon_tree)
        else:
            no_pages = int(imgfilename.split('_')[3])
            # Read image file
            img = imread(imgfilename)
            master_table, taxon_tree = process_image(img, no_pages, args, ocrreader, master_table, taxon_tree)


    # Write Excel sheet to disk
    master_table.to_excel(PurePath(args["output"]).as_posix(), index=False)

    # If verbose mode then show all opened figures
    if args["verbose"]:
        plt.show()


if __name__ == '__main__':
    main()
