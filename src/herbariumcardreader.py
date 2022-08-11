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

# import sys
import argparse
from skimage.io import imread, imsave
from skimage.util import img_as_ubyte
import matplotlib.pyplot as plt
import pandas as pd
import re
from pathlib import PurePath, Path

# Adding path to ocr package - this can probably be done smarter
# from pathlib import Path
# print("Adding to syspath: " + str(Path(__file__).parent.parent))
# sys.path.append(str(Path(__file__).parent.parent))

from labelreader.ocr import tesseract
from labelreader.labeldetect import labeldetect


def empty_dataframe():
    record = pd.DataFrame({
        "Catalogue Number": [],
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
        "Collector Last Name": [],
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



def parsetext(ocrtext):
    """Parses the transcribed text from a paper card into appropriate data fields.

       ocrtext: A list of lists of strings - one for each line on the paper card.
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
    genus = ""
    if len(ocrtext[line_idx]) >= 1:
        genus = ocrtext[line_idx][word_idx]
        word_idx += 1

    species = ""
    if len(ocrtext[line_idx]) > 2:
        species = ocrtext[line_idx][word_idx]
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
                other += "\n"
            other += joined_line

    record = pd.DataFrame({
        "Catalogue Number": [""],
        "Alt Cat Number": [alt_cat_number],
        "Publish": [1],
        "Count": [""],
        "Other Remarks": [other],
        "Order": [""],
        "Family": ["Acanthaceae"],
        "Genus1": [genus],
        "Species1": [species],
        "Determiner First Name": [""],
        "Determiner Last Name": [""],
        "Determination Remarks": [det_remarks],
        "Country": [country],
        "Locality": [locality],
        "Start Date": [datetext],
        "Collector First Name": [""],
        "Collector Last Name": [""],
        "Attachment": [""]
    })

    return record


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
    ap.add_argument("-v", "--verbose", required=False, action='store_true', default=False,
                    help="If set the program is verbose and will print out debug information")

    args = vars(ap.parse_args())


    print("Using language = " + args["language"] + "\n")

    # Initialize the OCR reader object
    ocrreader = tesseract.OCR(args["tesseract"], args["language"], config='--oem 1 --psm 6')

    master_table = empty_dataframe()

    # Loop over a directory of images
    for imgfilename in args["image"]:
        print("Transcribing " + imgfilename)
        # Read image with filename args["image"]
        img = imread(imgfilename)

        if args["verbose"]:
            plt.figure()
            plt.imshow(img)



        ocrreader.read_image(img)

        ocrtext = ocrreader.get_text()

        if args["verbose"]:
            for i in range(len(ocrtext)):
                print(ocrtext[i])

        df = parsetext(ocrtext)


        # TODO: Write cropped image to output directory
        #  In case of no Alt Cat Number just pick a unique random file name
        #outfilename = df["Alt Cat Number"][0] + ".png"
        #imsave(PurePath(args["output"], outfilename).as_posix(), img_rgb)
        outfilename = Path(imgfilename).name
        df["Attachment"].iloc[0] = outfilename  # Add filename to data record

        # Add to master table
        master_table = pd.concat([master_table, df], axis=0)

    if args["verbose"]:
        plt.show()

    # Write Excel sheet to disk
    master_table.to_excel(PurePath(args["output"], "test.xlsx").as_posix(), index=False)


if __name__ == '__main__':
    main()
