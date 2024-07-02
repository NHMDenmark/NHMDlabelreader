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
import logging
import copy
from skimage.io import imread, imsave
from skimage.util import img_as_ubyte
from skimage.color import rgb2hsv
import matplotlib.pyplot as plt
import pandas as pd
import re
from pathlib import Path
import numpy as np
from scipy.stats import linregress
import skimage.measure  # Needed for label function and regionprop
from skimage.transform import EuclideanTransform, warp

# Adding path to ocr package - this can probably be done smarter
# from pathlib import Path
# print("Adding to syspath: " + str(Path(__file__).parent.parent))
# sys.path.append(str(Path(__file__).parent.parent))

from labelreader.ocr import tesseract
from labelreader.labeldetect import labeldetect
from labelreader.util.util import checkfilepath
from labelreader.taxonchecker import gbiftaxonchecker
from labelreader.util.util import isromandate, parseromandate


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
        "Author name": [],
        "Scientific name": [],
        "GBIF checked scientific name": [],
        "Determiner First Name": [],
        "Determiner Last Name": [],
        "Determination Date": [],
        "Country": [],
        "Locality": [],
        "OCR Start Date": [],
        "Start Date": [],
        "Collector First Name": [],
        "Collector Last Name": [],
        "Attachment": [],
        "Original front image": []
    })
    return record


def empty_back_columns(rows):
    record = pd.DataFrame({
        "Notes_back": ["" for x in range(rows)],
        "Attachment_back": ["" for x in range(rows)],
        "Original back image": ["" for x in range(rows)]
    })
    return record

def empty_back_dataframe():
    record = pd.DataFrame({
        "Alt Cat Number": [],
        "Notes_back": [],
        "Attachment_back": [],
        "Original back image": []
    })
    return record

def islocality(text):
    """Return true if text has the locality format used by Bøggild.
       Assume the locality text starts with 'D,'

        text: String to analyse
        Return: Boolean
    """
    if re.match('^D,(\w|\s|[.,])+', text):
        return True
    else:
        return False


def isauthor(text):
    """Return true if text is a taxonomic author.
       Assumes that author name starts with a capital letter and might be enclosed in parentheses.

        text: String to analyse
        Return: Boolean
    """
    if re.match('^\(?[A-ZÆØÅ.](\d|\w|\s|[.,)])*', text):
        return True
    else:
        return False


def iscatnumber(text):
    """Return true if text is a catalog number.

        text: String to analyse
        Return: Boolean
    """
    if re.match('^[.]?\d{6}', text):
        return True
    else:
        return False


def isdettext(text):
    """Return true if text is 'Det' or 'Det.'.

        text: String to analyse
        Return: Boolean
    """
    if re.match('^Det[.]?', text):
        return True
    else:
        return False



def parsefronttext(ocrtext):
    """Parses the transcribed text from the front of a paper card into appropriate data fields.

       ocrtext: A list of lists of strings - one for each line on the paper card.
       Return record: Returns a Pandas data frame with the parsed transcribed data.
    """

    taxonchecker = gbiftaxonchecker.GBIFTaxonChecker()

    if len(ocrtext) == 0:
        # If ocrtext is empty then stop here!
        return empty_dataframe()

    # Skip any beginning blank lines
    line_idx = 0
    for idx in range(0, len(ocrtext)):
        if not ocrtext[idx][0].isspace():
            line_idx = idx
            break

    # Parse first real line
    word_idx = 0
    alt_cat_number = ""
    #if ocrtext[line_idx][word_idx].isdigit():
    if iscatnumber(ocrtext[line_idx][word_idx]):
        res = re.search(r"\d{6}", ocrtext[line_idx][word_idx])
        alt_cat_number = res.string[res.start():res.end()]
        word_idx += 1

    genus = ""
    if len(ocrtext[line_idx]) > 1:
        genus = ocrtext[line_idx][word_idx]
        word_idx += 1

    species = ""
    if len(ocrtext[line_idx]) > 2:
        species = ocrtext[line_idx][word_idx]
        word_idx += 1

    author_name = ""
    if len(ocrtext[line_idx]) > word_idx:
        # Handle the case with species names containing more than one word
        for idx in range(word_idx, len(ocrtext[line_idx])):
            if isauthor(ocrtext[line_idx][idx]):
                author_name = ' '.join(ocrtext[line_idx][idx:])
                break
            else:
                species += " " + ocrtext[line_idx][idx]

    line_idx += 1 # Next line

    # Initialize variables
    ocrdatetext = ""
    ocrdetdatetext = ""
    country = "Denmark"
    locality = ""
    other = ""

    # Parse the remaining lines
    for idx in range(line_idx, len(ocrtext)):
        joined_line = ' '.join(ocrtext[idx])
        if isromandate(ocrtext[idx][0]):
            if len(ocrtext[idx]) == 1:
                ocrdatetext = joined_line
            else:
                ocrdatetext = ocrtext[idx][0]
                if len(ocrtext[idx]) >= 3:
                    if isdettext(ocrtext[idx][1]):
                        ocrdetdatetext = ocrtext[idx][2]
        elif islocality(joined_line):
            # Pass out country
            # locality = ' '.join(ocrtext[idx][1:])
            locality = ' '.join(ocrtext[idx][0:])
        elif joined_line.isspace():
            continue  # Skip empty lines
        else:
            # Add the remaining text to the Other Remarks field
            if len(other) > 0:
                other += "\n"
            other += joined_line

    # Convert date format
    datetext = parseromandate(ocrdatetext)

    # Check the taxon name
    # This gives less hits
    #checked_taxonname = taxonchecker.check_full_name(genus + " " + species + " " + author_name)
    # This gives more hits
    taxonname = genus + " " + species + " " + author_name
    checked_gbif_taxonname = taxonchecker.check_full_name(genus + " " + species)

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
        "Author name": [author_name],
        "Scientific name": [taxonname],
        "GBIF checked scientific name": [checked_gbif_taxonname],
        "Determiner First Name": ["Ole"],
        "Determiner Last Name": ["Bøggild"],
        "Determination Date": [ocrdetdatetext],
        "Country": [country],
        "Locality": [locality],
        "OCR Start Date": [ocrdatetext],
        "Start Date": [datetext],
        "Collector First Name": ["Ole"],
        "Collector Last Name": ["Bøggild"],
        "Attachment": [""],
        "Original front image": [""]
    })

    return record


def parsebacktext(ocrtext):
    """Parses the transcribed text from the back of a paper card into a notes data field.

       ocrtext: A list of lists of strings - one for each line on the paper card.
       Return record: Returns a Pandas data frame with the parsed transcribed data.
    """
    text = ""
    for line in ocrtext:
        text += ' '.join(line) + "\n"

    record = pd.DataFrame({
        "Alt Cat Number": [""],
        "Notes_back": [text],
        "Attachment_back": [""],
        "Original back image": [""]
    })
    return record

def find_red_line_orientation(labelID, label_img, segMask):
    """Finds the thick red line at the top of the card and estimate card orientation from this line.

        labelID: ID of the label in label_img we want to consider
        label_img: Image of connected components as produced by labeldetect.find_labels
        segMask: A binary segmentation mask of the label with values 0.0 or 1.0
    """
    # Construct a binary mask with pixels on the thick red line by some logical operations
    line_mask = np.logical_and(np.logical_not(np.logical_and(label_img == labelID, segMask == 1.0)), label_img == labelID)
    line_mask_improved = labeldetect.improve_binary_mask(line_mask, radius=1) # Remove spurious outlier pixels
    line_idx = np.transpose(np.nonzero(line_mask_improved))  # Nx2 array of line pixel indices

    if line_idx.shape[0] > 0:
        # fit a line by linear least squares regression
        line_fit = linregress(line_idx[:,0], line_idx[:,1])

        # Compute orientation of the line
        vec = np.array([1.0, line_fit.slope], dtype=float)
        vec = vec / np.linalg.norm(vec, ord=2)  # Normalize to unit vector
        return np.arctan2(vec[1], vec[0]) # Estimate orientation with a sign
    else:
        return 0.0


def resample_label_from_line(img, label_img, segMask):
    """Crop and rotate the label image to be axis aligned by resampling the label pixels.
        We assume that labels in images are rectangular, but can be oriented in anyway in the image.
        We also assume that the label contain a thick line that can be used for orientation.

       Parameters:
         img: Image to process as an ndarray in either grayscale or RGB format.
         label_img: Labelled connected compomnents image with unique label identifier as ndarray
                    with dtype=np.int64.
         segMask: A binary segmentation mask in which the thick line is visible as zeros inside the label.
       Returns:
         a list of numpy arrays with same number of channels as img which contain the resampled labels.
    """

    lst_resampled_labels = []

    props = skimage.measure.regionprops(label_img)

    # Loop through all labels ignoring the background segment
    for prop in props:
        label_id = prop.label
        centroid = prop.centroid
        axis_minor_length = prop.axis_minor_length
        axis_major_length = prop.axis_major_length
        bbox = prop.bbox
        area = prop.area

        # Use area and minor/major axis length to check if aspect ratio and area of region is reasonable
        #  otherwise discard
        if (axis_minor_length / axis_major_length < 0.8) and (area > 30000):
            # Compute orientation
            orientation = find_red_line_orientation(label_id, label_img, segMask)

            # Convert centroid from (row,col) to (x,y) representation
            center = -np.array([centroid[1], centroid[0]], dtype=float)

            # Find upper left corner of rotated bounding box
            corner = np.array([0.5 * axis_major_length, 0.5 * axis_minor_length], dtype=float)

            # Construct inverse homogeneous Euclidean transformation matrix to transform
            # label in img into a cropped and axis aligned image of this label
            trans_centroid = np.eye(3, dtype=float)
            trans_centroid[0, 2] = center[0]
            trans_centroid[1, 2] = center[1]
            rotate_crop = EuclideanTransform(rotation=(orientation + np.pi / 2.0), translation=corner)

            # Combined transform
            transf = np.dot(rotate_crop.params, trans_centroid)
            # The inverse of the combined transform
            inv_transf = np.linalg.inv(transf)

            # Crop and rotate image
            # TODO: Consider rounding output_shape instead of truncating to integer - Does not seem to be important
            warped = warp(img, inv_transf, output_shape=(int(axis_minor_length), int(axis_major_length)))

            # Add region properties to a dictionary together with image of label
            label_data = dict()  # Create a new empty dictionary object
            label_data['label_id'] = label_id
            label_data['orientation'] = orientation
            label_data['centroid'] = centroid
            label_data['axis_minor_length'] = axis_minor_length
            label_data['axis_major_length'] = axis_major_length
            label_data['bbox'] = bbox
            label_data['area'] = area
            label_data['image'] = warped

            # Append cropped image of label to lst_resampled_labels.
            lst_resampled_labels.append(label_data)

    return lst_resampled_labels


def estimateBackgroundColor(img, width=200, height=200):
    """Compute an estimate of the background color by averaging pixel values in a rectangle in the upper
       left corner of the image

        img: Image the process
        width, height: Sampling rectangle size in pixels
        Return: A 3-vector as a numpy array with shape (3,) containing the average Hue-Saturation-Value in the
                rectangle
    """
    mean_rgb = np.mean(img[0:height, 0:width,:], axis=(0,1))
    return rgb2hsv(mean_rgb)

def findClosestLabel(label_data, previous_lst_labels):
    """Find the label closest to label_data in the provided list

        label_data: Label dictionary to find a match for
        previous_lst_labels: List of label dictionaries to compare to
        Return: The Alt Cat Number from the matching label dictionary. Returns empty string if no match.
    """
    shortest_cat_number = ""
    shortest_dist = 10**64
    for previous_label_data in previous_lst_labels:
        dist = np.linalg.norm(np.array(label_data["centroid"]) - np.array(previous_label_data["centroid"]))
        if dist < shortest_dist:
            shortest_dist = dist
            shortest_cat_number = previous_label_data["Alt Cat Number"]

    return shortest_cat_number


def main():
    """The main function of this script."""
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser(description="Transcribe Bøggild catalogue cards from images.")
    ap.add_argument("-t", "--tesseract", required=True,
                    help="path to tesseract executable")
    ap.add_argument("-i", "--image", required=True, action="extend", nargs="+", type=str,
                    help="file name for and path to input image")
    ap.add_argument("-o", "--output", required=False, default="../output",
                    help="path to write results in the form of Excel spreadsheet and individual label images.")
    ap.add_argument("-l", "--language", required=False, default="dan+eng",
                    help="language that tesseract uses - depends on installed tesseract language packages")
    ap.add_argument("-r", "--resolution", required=False, default=400, type=int,
                    help="Set resolution in DPI of scanned images - used for rendering pdf pages so only relevant for PDF files")
    ap.add_argument("-v", "--verbose", required=False, action='store_true', default=False,
                    help="If set the program is verbose and will print out debug information")

    args = vars(ap.parse_args())

    if args["verbose"]:
        #logging.basicConfig(encoding='utf-8', level=logging.DEBUG)
        logging.basicConfig(level=logging.INFO)
    else:
        #logging.basicConfig(encoding='utf-8', level=logging.WARN)
        logging.basicConfig(level=logging.WARNING)

    print("Using language = " + args["language"] + "\n")

    # Initialize the OCR reader object
    ocrreader = tesseract.OCR(args["tesseract"], args["language"], config='--oem 3')
    # ocrreader = tesseract.OCR(args["tesseract"], args["language"], config='--oem 2')
    # ocrreader = tesseract.OCR(args["tesseract"], args["language"], config='--oem 1 --psm 6')

    # Initialize variables
    master_table = empty_dataframe()
    lst_resampled_labels = []
    previous_lst_resampled_labels = []
    previous_image_was_front = False
    front_table = None
    image_table = empty_dataframe()

    image_count = 0

    # Loop over a directory of images
    for imgfilename in args["image"]:
        # Read image with filename
        print("Transcribing " + Path(imgfilename).name)
        img = imread(imgfilename)

        # Estimate background color and perform different processing depending on this
        mean_hsv = estimateBackgroundColor(img)
        backgroundIsBlue = mean_hsv[0] > 0.5
        if backgroundIsBlue: # Blue background
            print("Blue background")
            segMask = labeldetect.color_segment_labels(img, huerange=(0.5, 0.7))  # Light blue background
        else: # Red background
            print("Red background")
            segMask = labeldetect.color_segment_labels(img) # Red background

        # Find labels by color segmentation
        segMaskImproved = labeldetect.improve_binary_mask(segMask)
        label_img, num_labels = labeldetect.find_labels(segMaskImproved)

        # Improve orientation estimation by finding the red line
        if backgroundIsBlue:
            lineMask = labeldetect.color_segment_labels(img) # Segment red lines on labels
            previous_lst_resampled_labels = copy.deepcopy(lst_resampled_labels) # Keep for later label location look-up
        else:
            # For red background, reuse the initial segMask
            lineMask = segMask

        # Segment individual labels and rotate appropriately
        lst_resampled_labels = resample_label_from_line(img, label_img, lineMask)

        if args["verbose"]:
            plt.figure()
            plt.imshow(img)
            plt.title(Path(imgfilename).name)

            plt.figure()
            plt.imshow(segMask)
            plt.title("segMask")

            if backgroundIsBlue:
                plt.figure()
                plt.imshow(lineMask)
                plt.title("lineMask")

            plt.figure()
            plt.imshow(label_img)
            plt.title("label_img")

            # logging.info("number of labels detected: " + str(len(lst_resampled_labels)))
            print("number of labels detected: " + str(len(lst_resampled_labels)))

        if not len(lst_resampled_labels) == 9:
            logging.warning("Warning: Wrong number of detected labels = " + str(len(lst_resampled_labels)))
            # print("Warning: Wrong number of detected labels = " + str(len(lst_resampled_labels)))
            # return  # TODO: Maybe use exit with a non-zero exit code (for later use in shell scripts)


        if backgroundIsBlue:
            if previous_image_was_front:
                front_table = image_table.copy()
            else:
                front_table = empty_dataframe()

            image_table = empty_back_dataframe()
        else:
            if previous_image_was_front:
                # Add empty backside columns to table
                #image_table = pd.concat([image_table, empty_back_columns(len(lst_resampled_labels))], axis=1)

                # Add to master table
                #master_table = pd.concat([master_table, image_table], axis=0, ignore_index=True)
                master_table = pd.concat([master_table, image_table], axis=0)

            image_table = empty_dataframe()

        for label_data in lst_resampled_labels:
            if args["verbose"]:
                print("")
                print("ID " + str(label_data["label_id"]) + " orientation " + str(label_data['orientation'])
                      + " coord " + str(label_data['centroid']))

            img_label = img_as_ubyte(label_data['image'])
            ocrreader.read_image(img_label)

            ocrtext = ocrreader.get_text()

            if args["verbose"]:
                for i in range(len(ocrtext)):
                    print(ocrtext[i])

            if backgroundIsBlue:
                df = parsebacktext(ocrtext)
                # Figure out which Alt Cat Number to update with background info
                # Add Alt Cat Number to data record
                foundAltCatNumber = findClosestLabel(label_data, previous_lst_resampled_labels)
                if args["verbose"]:
                    print("Closest Alt Cat Number is " + foundAltCatNumber)

                df.at[0,"Alt Cat Number"] = foundAltCatNumber
                suffix = "_back"
            else:
                df = parsefronttext(ocrtext)

                if args["verbose"]:
                    print("df.shape = " + str(df.shape))

                # Save the alternative catalogue number for back processing
                # Assumes that a Python list contains references
                if not df.empty:
                    label_data["Alt Cat Number"] = df["Alt Cat Number"][0]
                    suffix = ""

            if not df.empty:

                #  In case of no Alt Cat Number just pick a unique file name
                if df["Alt Cat Number"][0] == "":
                    outfilename = Path(imgfilename).stem + "_labelID" + str(label_data["label_id"]) + suffix + ".tif"
                else:
                    outfilename = df["Alt Cat Number"][0] + suffix + ".tif"

                # Check that filename is unique otherwise create an extension of it to make unique
                outpath = Path(args["output"], outfilename)
                outpath = checkfilepath(outpath)
                outfilename = outpath.name

                # Save image
                imsave(str(outpath), img_label, check_contrast=False, plugin='pil', compression="tiff_lzw",
                   resolution_unit=2, resolution=400)
                # Add to Attachment and Original image columns to handle front and back label images
                if backgroundIsBlue:
                    df.at[0, "Attachment_back"] = outfilename # Add filename to data record

                    # Add original image file name to data record
                    df.at[0, "Original back image"] = Path(imgfilename).name
                else:
                    df.at[0, "Attachment"] = outfilename  # Add filename to data record

                    # Add original image file name to data record
                    df.at[0, "Original front image"] = Path(imgfilename).name



                # Add to image table
                image_table = pd.concat([image_table, df], axis=0, ignore_index=True)

            # ocrreader.visualize_boxes()

            if args["verbose"]:
                plt.figure()
                plt.imshow(label_data['image'])
                plt.title("ID " + str(label_data["label_id"]))


        if backgroundIsBlue:
            # Merge to previous image table
            image_table = front_table.join(image_table.set_index("Alt Cat Number"), on="Alt Cat Number", how='left')

            # Add to master table
            master_table = pd.concat([master_table, image_table], axis=0, ignore_index=True)

            previous_image_was_front = False
        else:
            #if previous_image_was_front:
            #    # Add empty backside columns to table
            #    image_table = pd.concat([image_table, empty_back_columns(len(lst_resampled_labels))], axis=1)

            previous_image_was_front = True

        # Write a snapshot as Excel sheet to disk
        master_table.to_excel(str(Path(args["output"], "spidercards.xlsx")), index=False)

        image_count+=1
        print("Processed " + str(image_count) + " images")


    if args["verbose"]:
        plt.show()

    if previous_image_was_front:
        # Add to master table
        master_table = pd.concat([master_table, image_table], axis=0, ignore_index=True)

    # Write final table to disk as Excel sheet
    master_table.to_excel(str(Path(args["output"], "spidercards.xlsx")), index=False)

if __name__ == '__main__':
    main()
