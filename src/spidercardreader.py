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
from skimage.io import imread, imsave
from skimage.util import img_as_ubyte
import matplotlib.pyplot as plt
import pandas as pd
import re
from pathlib import Path

# Adding path to ocr package - this can probably be done smarter
# from pathlib import Path
# print("Adding to syspath: " + str(Path(__file__).parent.parent))
# sys.path.append(str(Path(__file__).parent.parent))

from labelreader.ocr import tesseract
from labelreader.labeldetect import labeldetect
from util.util import checkfilepath


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



def parsefronttext(ocrtext):
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
    word_idx = 0
    alt_cat_number = ""
    if ocrtext[line_idx][word_idx].isdigit():
        alt_cat_number = ocrtext[line_idx][word_idx]
        word_idx += 1

    genus = ""
    if len(ocrtext[line_idx]) > 1:
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

    # Initialize variables
    datetext = ""
    country = "Denmark"
    locality = ""
    other = ""

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
        "Order": ["Araneae"],
        "Family": [""],
        "Genus1": [genus],
        "Species1": [species],
        "Determiner First Name": ["Ole"],
        "Determiner Last Name": ["Bøggild"],
        "Determination Remarks": [det_remarks],
        "Country": [country],
        "Locality": [locality],
        "Start Date": [datetext],
        "Collector First Name": ["Ole"],
        "Collector Last Name": ["Bøggild"],
        "Attachment": [""]
    })

    return record


def main():
    """The main function of this script."""
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser(description="Transcribe Bøggild catalogue cards from images.")
    ap.add_argument("-t", "--tesseract", required=True,
                    help="path to tesseract executable")
    ap.add_argument("-i", "--image", required=True, action="extend", nargs="+", type=str,
                    help="file name for and path to input image")
    ap.add_argument("-o", "--output", required=False, default="../output",
                    help="path and filename for Excel spreadsheet to write result to.")
    ap.add_argument("-l", "--language", required=False, default="dan+eng",
                    help="language that tesseract uses - depends on installed tesseract language packages")
    ap.add_argument("-r", "--resolution", required=False, default=400, type=int,
                    help="Set resolution in DPI of scanned images - used for rendering pdf pages so only relevant for PDF files")
    ap.add_argument("-v", "--verbose", required=False, action='store_true', default=False,
                    help="If set the program is verbose and will print out debug information")

    args = vars(ap.parse_args())


    print("Using language = " + args["language"] + "\n")

    # Initialize the OCR reader object
    ocrreader = tesseract.OCR(args["tesseract"], args["language"])

    master_table = empty_dataframe()

    # Loop over a directory of images
    for imgfilename in args["image"]:
        # Read image with filename
        print("Transcribing " + imgfilename)
        img = imread(imgfilename)

        # TODO: handle front (red) and back (blue)
        segMask = labeldetect.color_segment_labels(img) # Red background
        #segMask = labeldetect.color_segment_labels(img, huerange=(0.5, 0.6)) # Light blue background
        segMask = labeldetect.improve_binary_mask(segMask)
        label_img, num_labels = labeldetect.find_labels(segMask)
        lst_resampled_labels = labeldetect.resample_label(img, label_img, num_labels)

        if args["verbose"]:
            plt.figure()
            plt.imshow(img)

            plt.figure()
            plt.imshow(label_img)

            print("number of labels detected: " + str(len(lst_resampled_labels)))

        if not len(lst_resampled_labels) == 9:
            print("Warning: Too many detected labels ...")
            #return  # TODO: Maybe use exit with a non-zero exit code (for later use in shell scripts)


        for label_data in lst_resampled_labels:
            if args["verbose"]:
                print("")
                print("ID " + str(label_data["label_id"]) + " orientation " + str(label_data['orientation']) + " coord " + str(label_data['centroid']))

            img_label = img_as_ubyte(label_data['image'])
            ocrreader.read_image(img_label)

            ocrtext = ocrreader.get_text()

            if args["verbose"]:
                for i in range(len(ocrtext)):
                    print(ocrtext[i])

            df = parsefronttext(ocrtext)


            #  In case of no Alt Cat Number just pick a unique file name
            if df["Alt Cat Number"][0] == "":
                outfilename = Path(imgfilename).stem + "_labelID" + str(label_data["label_id"]) + ".tif"
            else:
                outfilename = df["Alt Cat Number"][0] + ".tif"

            # Check that filename is unique otherwise create an extension of it to make unique
            outpath = Path(args["output"], outfilename)
            outpath = checkfilepath(outpath)
            outfilename = outpath.name
            imsave(str(outpath), img_label, check_contrast=False, plugin='pil', compression="tiff_lzw",
                   resolution_unit=2, resolution=400)
            df["Attachment"].update(pd.Series([outfilename], index=[0]))  # Add filename to data record

            # Add to master table
            master_table = pd.concat([master_table, df], axis=0, ignore_index=True)

            #ocrreader.visualize_boxes()

            if args["verbose"]:
                plt.figure()
                plt.imshow(label_data['image'])
                plt.title("ID " + str(label_data["label_id"]))

    if args["verbose"]:
        plt.show()

    # Write Excel sheet to disk
    master_table.to_excel(str(Path(args["output"], "test.xlsx")), index=False)


if __name__ == '__main__':
    main()
