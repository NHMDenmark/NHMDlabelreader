# -*- coding: utf-8 -*-
"""
Created on Thu Aug 21 14:48:00 2022

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

import argparse
from skimage.io import imread, imsave
#from skimage.util import img_as_ubyte
import matplotlib.pyplot as plt
import pandas as pd
import re
from pathlib import PurePath, Path
from wand.image import Image
import numpy as np

# Adding path to ocr package - this can probably be done smarter
# from pathlib import Path
# print("Adding to syspath: " + str(Path(__file__).parent.parent))
# sys.path.append(str(Path(__file__).parent.parent))

from labelreader.ocr import tesseract
#from labelreader.labeldetect import labeldetect
from labelreader.util.util import checkfilepath
from labelreader.taxonchecker import dbtaxonchecker


def empty_dataframe():
    record = pd.DataFrame({
        "Catalogue Number": [],
        "Alt Cat Number": [],
        "Publish": [],
        "Other Remarks": [],
        "Order": [],
        "Family": [],
        "Genus1": [],
        "Species1": [],
        "Determination Remarks": [],
        "OCR full name": [],
        "Corrected full name": [],
        "Fuzzy match percentage": [],
        "Determiner": [],
        "Collector": [],
        "Country": [],
        "Locality": [],
        "Start Date": [],
        "Attachment": []
    })
    return record


def is_nodot(text):
    """Return true if text starts with 'No.' as used by NHMD Botany.

        text: String to analyse
        Return: Boolean
    """
    if re.match('No.', text):
        return True
    else:
        return False

def is_nodot_number(text):
    """Return true if text starts with 'No. ' followed by a number as used by NHMD Botany.

        text: String to analyse
        Return: Boolean
    """
    if re.match('No. \d+', text):
        return True
    else:
        return False


def iscataloguenumber(text):
    """Return true if text has the catalogue number format used by NHMD Botany.
       Assume format is digits possible separated by '.' or '-'.

        text: String to analyse
        Return: Boolean
    """
    if re.match('\d+[.-]*\d+', text):
        return True
    else:
        return False

def isdate(text):
    """Return true if text has the date format used by Bøggild.
       Assume format is one or two digits for Day, Roman numeral for Month and 4 digits for Year.

        text: String to analyse
        Return: Boolean
    """
    # Assume format is one or two digits for Day, Roman numeral for Month and 4 digits for Year
    # Include a common OCR mistake of reading I as 1 as acceptable.
    if re.match('\d{1,2}.[IVX1]+.\d{4}', text):
        return True
    else:
        return False

def islocality(text):
    """Return true if text has the locality format used by Bøggild.
       Assume the locality text starts with 'D,'

        text: String to analyse
        Return: Boolean
    """
    if re.match('D,(\w|\s|[.,])+', text):
        return True
    else:
        return False


def isauthor(text):
    """Return true if text is a taxonomic author.
       Assumes that author is inclosed in parentheses.

        text: String to analyse
        Return: Boolean
    """
    if re.match('\((\d|\w|\s|[.,)])*', text):
        return True
    else:
        return False



def letters_only(text):
    """Clean the text and return a version with only letters.

        text: String to clean
        Return: A cleaned string
    """
    return ''.join([c for c in text if c.isalpha()])


def parsetext(ocrtext, checker):
    """Parses the transcribed text from a paper card into appropriate data fields.

       ocrtext: A list of lists of strings - one for each line on the paper card.
       checker: A TaxonChecker object
       Return record: Returns a Pandas data frame with the parsed transcribed data.
    """

    # Initialize variables
    datetext = ""
    country = ""
    locality = ""
    other = ""

    # Skip any beginning blank lines
    line_idx = 0
    for idx in range(0, len(ocrtext)):
        if not ocrtext[idx][0].isspace():
            line_idx = idx
            break

    # Parse first real line
    alt_cat_number = ""
    for elem in ocrtext[line_idx]:
        if iscataloguenumber(elem):
            alt_cat_number = elem

    # Parse second line
    line_idx += 1 # Next line
    word_idx = 0

    if len(ocrtext[line_idx]) == 2 and (is_nodot(ocrtext[line_idx][word_idx]) and ocrtext[line_idx][word_idx+1].isdigit()):
        other+= ocrtext[line_idx][word_idx] + " " + ocrtext[line_idx][word_idx+1]
        line_idx += 1  # Next line
        word_idx = 0

    # Parse taxon line
    corrected_fullname = ""
    genus = ""
    if len(ocrtext[line_idx]) >= 1:
        genus = ocrtext[line_idx][word_idx].lower().capitalize()
        # res = checker.check_name(genus)
        # if not isinstance(res, type(None)):
        #    corrected_fullname += res[0]

        word_idx += 1

    species = ""
    if len(ocrtext[line_idx]) > 2:
        species = ocrtext[line_idx][word_idx].lower()
        # res = checker.check_name(species)
        # if not isinstance(res, type(None)):
        #    corrected_fullname += res[0]

        word_idx += 1

    det_remarks = ""
    if len(ocrtext[line_idx]) > word_idx:
        # Handle the case with species names containing more than one word
        for idx in range(word_idx, len(ocrtext[line_idx])):
            if isauthor(ocrtext[line_idx][idx]):
                det_remarks = ' '.join(ocrtext[line_idx][idx:])
                break
            else:
                species += " " + ocrtext[line_idx][idx]

    line_idx += 1 # Next line
    if len(species)==0:
        for idx in range(0, len(ocrtext[line_idx])):
            if isauthor(ocrtext[line_idx][idx]):
                det_remarks += ' '.join(ocrtext[line_idx][idx:])
                break
            else:
                species += " " + ocrtext[line_idx][idx]

        line_idx +=1 # Next line


    # Parse the remaining lines
    for idx in range(line_idx, len(ocrtext)):
        joined_line = ' '.join(ocrtext[idx])
        if isdate(joined_line):
            datetext = joined_line
        elif islocality(joined_line):
            # Pass out country
            locality = ' '.join(ocrtext[idx][1:])
        elif joined_line.isspace():
            continue  # Skip empty lines
        else:
            # Add the remaining text to the Other Remarks field
            if len(other) > 0:
                other += "; "
            other += joined_line


    # Clean up the genus name
    genus = letters_only(genus)

    # check taxonomic full name
    ocr_fullname = " ".join([genus, species, det_remarks])
    res = checker.check_full_name(ocr_fullname)
    fuzzy_score = 0
    # print(res)
    if not isinstance(res, type(None)):
        corrected_fullname = res[0]
        fuzzy_score = res[1]

    record = pd.DataFrame({
        "Catalogue Number": [""],
        "Alt Cat Number": [alt_cat_number],
        "Publish": [1],
        "Other Remarks": [other],
        "Order": [""],
        "Family": ["Acanthaceae"],
        "Genus1": [genus],
        "Species1": [species],
        "Determination Remarks": [det_remarks],
        "OCR full name": [ocr_fullname],
        "Corrected full name": [corrected_fullname],
        "Fuzzy match percentage": [fuzzy_score],
        "Determiner": [""],
        "Collector": [""],
        "Country": [country],
        "Locality": [locality],
        "Start Date": [datetext],
        "Attachment": [""]
    })

    return record


def process_image(img, imgfilename, no_img, no_pages, args, ocrreader, master_table, checker):
    """Parse one image and create a row in the master_table"""
    if args["verbose"]:
        plt.figure()
        plt.imshow(img)

    ocrreader.read_image(img)

    ocrtext = ocrreader.get_text()

    if args["verbose"]:
        for i in range(len(ocrtext)):
            print(ocrtext[i])

    df = parsetext(ocrtext, checker)

    #  In case of no Alt Cat Number just pick a unique random file name
    if df["Alt Cat Number"][0] == "":
        outfilename = Path(imgfilename).stem + "_image" + str(no_img) + "_page" + str(no_pages) + ".tif"
    else:
        outfilename = df["Alt Cat Number"][0] + ".tif"

    # Check that filename is unique otherwise create an extension of it to make unique
    outpath = Path(args["output"], outfilename)
    outpath = checkfilepath(outpath)
    outfilename = outpath.name

    imsave(str(outpath), img, check_contrast=False, plugin='pil', compression="tiff_lzw",
           resolution_unit=2, resolution=args["resolution"])
    df["Attachment"].update(pd.Series([outfilename], index=[0]))  # Add filename to data record

    # Add to master table
    master_table = pd.concat([master_table, df], axis=0, ignore_index=True)

    return master_table


def main():
    """The main function of this script."""
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser(description="Transcribe NHMD Herbarium catalogue cards from images.")
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
    ocrreader = tesseract.OCR(args["tesseract"], args["language"], config='--oem 1 --psm 6')

    # Initialize taxon checker
    checker = dbtaxonchecker.DBTaxonChecker(dbfilename=str(Path.cwd().parent.joinpath("db").joinpath("db.sqlite3")))

    master_table = empty_dataframe()

    # Loop over a directory of images
    no_img = 0 # Count number of images
    no_pages = 0 # Count number of pages
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
                    master_table = process_image(img, imgfilename, no_img, no_pages, args, ocrreader, master_table, checker)

        elif Path(imgfilename).suffix == '.tif':
            # Read image file
            img = imread(imgfilename, plugin='pil')
            master_table = process_image(img, imgfilename, no_img, no_pages, args, ocrreader, master_table, checker)
        else:
            # Read image file
            img = imread(imgfilename)
            master_table = process_image(img, imgfilename, no_img, no_pages, args, ocrreader, master_table, checker)


    # If verbose mode then show all opened figures
    if args["verbose"]:
        plt.show()

    # Write Excel sheet to disk
    master_table.to_excel(PurePath(args["output"], "output.xlsx").as_posix(), index=False)


if __name__ == '__main__':
    main()
