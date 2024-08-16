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

import pandas
from skimage.io import imread, imsave
import matplotlib.pyplot as plt
import pandas as pd
import re
from pathlib import PurePath, Path
from wand.image import Image
import numpy as np
import lark

# Adding path to ocr package - this can probably be done smarter
# from pathlib import Path
# print("Adding to syspath: " + str(Path(__file__).parent.parent))
# sys.path.append(str(Path(__file__).parent.parent))

from labelreader.ocr import tesseract
from labelreader.util.util import checkfilepath
from labelreader.taxonchecker import gbiftaxonchecker
from labelreader.util.util import isromandate, parseromandate, isdettext, islegtext, islegdettext, iscolltext


def empty_dataframe():
    record = pd.DataFrame({
        "Alt Cat Number": [],
        "Other Remarks": [],
        "Family": [],
        "Genus": [],
        "Species": [],
        "Subspecies": [],
        "Author name": [],
        "Scientific name": [],
        "GBIF checked scientific name": [],
        "Determiner": [],
        "Collector": [],
        "Number": [],
        "Locality": [],
        "Date": [],
        "Parsed date": [],
        "Attachment": []
    })
    return record


def is_nodot(text):
    """Return true if text starts with 'No.' as used by NHMD Botany.

        text: String to analyse
        Return: Boolean
    """
    if re.match('No\.', text):
        return True
    else:
        return False

def is_nodot_number(text):
    """Return true if text starts with 'No. ' followed by a number as used by NHMD Botany.

        text: String to analyse
        Return: Boolean
    """
    if re.match('No\.[ ]?\d{3}', text):
        return True
    else:
        return False


def iscataloguenumber(text):
    """Return true if text has the catalogue number format used by NHMD Botany.
       Assume format is digits possible separated by '.' or '-'.

        text: String to analyse
        Return: Boolean
    """
    if re.match('\d+([.]?\d+)?([-]\d+)?', text):
        return True
    elif re.match('(\w)+\d+[.-]*\d+', text):
        return True
    else:
        return False

def iscataloguecode(text):
    """Return true if text has the catalogue code format used by NHMD Botany.

            text: String to analyse
            Return: Boolean
        """
    if re.match('(Pt[.]?(\s)?(\+|&)(\s)?G[.]?)|(G[.]?(\s|-)+tør(saml)?[.]?)', text):
        return True
    else:
        return False

def isdate(text):
    """Return true if text has the date format used by NHMD Botany.
       The format can be any of the normal date formats used in the world as well as roman numeral for month format.

        text: String to analyse
        Return: Boolean
    """
    # Include a common OCR mistake of reading I as 1 as acceptable.
    if isromandate(text): # Allow for roman numerals format
        return True
    elif re.match('\d{1,2}[ .,/]\d{1,2}[ .,/-]\d{2,4}', text): # Allow for day and month numerals format
        return True
    elif re.match('(\d{1,2})?[ .,/]?(\w)*[ .,/-]\d{2,4}', text): # Allow for month name
        return True
    elif re.match('(\w)+[.]*(\s)*\d{2,4}', text): # Allow for month name and year only
        return True
    elif re.match('\d{2,4}[-/]\d{2}', text): # Allow for year range
        return True
    elif re.match('\d{4}[.,]?', text): # Allow for year only
        return True
    else:
        return False

def lastcharispunctuation(text):
    """Return true if the last character in the text is a punctuation character '.' or ','.

        text: String to analyse
        Return: Boolean
    """
    if re.match('.*[.,]$', text):
        return True
    else:
        return False

def islocality(text): # TODO: Adjust to the NHMD Botany format
    """Return true if text has the locality format used by Bøggild.
       Assume the locality text starts with 'D,'

        text: String to analyse
        Return: Boolean
    """
    if re.match('D,(\w|\s|[.,])+', text):
        return True
    else:
        return False


def isauthor(text): # TODO: This is too restrictive
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

def parsetext(ocrtext, family, checker):
    """Parses the OCR text from a paper card into appropriate data fields.

       ocrtext: A list of lists of strings - one for each line on the paper card.
       family: A string with the taxonomic family name of the plant
       checker: A TaxonChecker object
       Return record: Returns a Pandas data frame with the parsed transcribed data.
    """

    # If ocrtext is empty then stop here!
    if len(ocrtext) == 0:
        return empty_dataframe()

    # Initialize variables
    datetext = ""
    locality = ""
    col_number = ""
    other = ""

    # Skip any beginning blank lines
    line_idx = 0
    for idx in range(0, len(ocrtext)):
        if not ocrtext[idx][0].isspace():
            line_idx = idx
            break

    # Parse first real line for catalogue number
    alt_cat_number = ""
    #for elem in ocrtext[line_idx]:
    for word_idx in range(0, len(ocrtext[line_idx])):
        if iscataloguenumber(ocrtext[line_idx][word_idx]):
            alt_cat_number = ocrtext[line_idx][word_idx]
        elif iscataloguecode(ocrtext[line_idx][word_idx]):
            if len(ocrtext[line_idx]) > word_idx+1:
                if iscataloguenumber(ocrtext[line_idx][word_idx+1]):
                    alt_cat_number = ocrtext[line_idx][word_idx] + " " + ocrtext[line_idx][word_idx+1]

    # Parse second line
    # Assume either Taxon name or No. and number
    line_idx += 1 # Next line
    word_idx = 0

    # Check for No. and number
    if len(ocrtext[line_idx]) == 2 and (is_nodot(ocrtext[line_idx][word_idx]) and ocrtext[line_idx][word_idx+1].isdigit()):
        col_number = ocrtext[line_idx][word_idx] + " " + ocrtext[line_idx][word_idx+1]
        line_idx += 1  # Next line
        word_idx = 0

    # Parse taxon line
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
    if len(species)==0 and not lastcharispunctuation(genus):
        for idx in range(0, len(ocrtext[line_idx])):
            if isauthor(ocrtext[line_idx][idx]):
                author_name += ' '.join(ocrtext[line_idx][idx:])
                break
            else:
                species += " " + ocrtext[line_idx][idx]

        line_idx +=1 # Next line


    collector = ""
    determiner = ""

    # Parse the remaining lines
    for idx in range(line_idx, len(ocrtext)):
        joined_line = ' '.join(ocrtext[idx])
        if joined_line.isspace():
            continue  # Skip empty lines
        elif is_nodot_number(joined_line):
            col_number = joined_line
        elif isdate(joined_line):
            if isromandate(joined_line):
                datetext = parseromandate(joined_line)
            else:
                datetext = joined_line
        elif islegdettext(joined_line):
            determiner = joined_line
            collector = joined_line
        elif isdettext(joined_line) or re.match('^(D|d)ed[.]?[:]?', joined_line): # Handle typo in Ded.
            determiner = joined_line
        elif islegtext(joined_line) or iscolltext(joined_line):
            collector = joined_line
        elif islocality(joined_line):
            # Pass out country
            locality = ' '.join(ocrtext[idx][1:])
        else:
            # Add the remaining text to the Other Remarks field
            if len(other) > 0:
                other += "; "
            other += joined_line


    # Clean up the genus name
    genus = letters_only(genus)

    # check taxonomic full name
    ocr_taxonname = " ".join([genus, species, author_name])
    checked_gbif_taxonname = checker.check_full_name(" ".join([genus, species]))


    record = pd.DataFrame({
        "Alt Cat Number": [alt_cat_number],
        "Other Remarks": [other],
        "Family": [family],
        "Genus": [genus],
        "Species": [species],
        "Subspecies": [""],
        "Author name": [author_name],
        "Scientific name": [ocr_taxonname],
        "GBIF checked scientific name": [checked_gbif_taxonname],
        "Determiner": [determiner],
        "Collector": [collector],
        "Number": [col_number],
        "Locality": [locality],
        "Date": [datetext],
        "Parsed date": [""],
        "Attachment": [""]
    })

    return record



def larkparsetext(ocrtext: str, family: str, checker: str) -> pandas.DataFrame:
    """Parses the OCR text from a paper card into appropriate data fields using the Lark parser generator
        and a context-free grammar.

       ocrtext: A list of lists of strings - one for each line on the paper card.
       family: A string with the taxonomic family name of the plant
       checker: A TaxonChecker object
       Return record: Returns a Pandas data frame with the parsed transcribed data.
    """

    # If ocrtext is empty then stop here!
    if len(ocrtext) == 0:
        return empty_dataframe()

    # Initialize variables
    alt_cat_number = ""
    other = ""
    genus = ""
    species = ""
    subspecies = ""
    author_name = ""
    determiner = ""
    collector = ""
    col_number = ""
    locality = ""
    datetext = ""
    parseddate = ""


    # Read the grammar and create the parser
    gf = open("../grammars/csad.lark", "r")
    grammar = gf.read()
    parser = lark.Lark(grammar, start='card')

    # Create a text string from the list of lists from the OCR
    text = ""
    for idx in range(0, len(ocrtext)):
        text += " ".join(ocrtext[idx]) + "\n"

    # Create the parse tree
    ptree = parser.parse(text)

    # Process the parse tree
    for child in ptree.children:
        if not isinstance(child, lark.Token):
            if child.data == "top_line":
                for grandchildren in child.children:
                    if not isinstance(grandchildren, lark.Token):
                        for grandchild in grandchildren.children:
                            if grandchildren.data == "family":
                                family = str(grandchild)
                            elif grandchildren.data == "catcode":
                                alt_cat_number += str(grandchild)
                            elif grandchildren.data == "catnumber":
                                alt_cat_number += " " + str(grandchild)
            elif child.data == "nodot":
                col_number = str(child.children[0])
            elif child.data == "taxon_lines":
                for grandchildren in child.children:
                    if not isinstance(grandchildren, lark.Token):
                        if grandchildren.data == "genus":
                            genus = str(grandchildren.children[0])
                        elif grandchildren.data == "species":
                            species = str(grandchildren.children[0])
                        elif grandchildren.data == "subspecies":
                            subspecies = str(grandchildren.children[0])
                        elif grandchildren.data == "author":
                            author_name = str(grandchildren.children[0])
                        elif grandchildren.data == "taxon_lines":
                            for grandchild in grandchildren.children:
                                if not isinstance(grandchild, lark.Token):
                                    if grandchild.data == "species":
                                        species = str(grandchild.children[0])
                                    elif grandchild.data == "subspecies":
                                        subspecies = str(grandchild.children[0])
                                    elif grandchild.data == "author":
                                        author_name = str(grandchild.children[0])
            elif child.data == "line":
                for grandchildren in child.children:
                    if not isinstance(grandchildren, lark.Token):
                        if grandchildren.data == "nodot":
                            col_number = str(grandchildren.children[0])
                        elif grandchildren.data == "leg":
                            collector = str(grandchildren.children[1].children[0])
                        elif grandchildren.data == "det":
                            determiner = str(grandchildren.children[1].children[0])
                        elif grandchildren.data == "legdet":
                            collector = str(grandchildren.children[1].children[0])
                            determiner = collector
                        elif grandchildren.data == "date_string":
                            for datecomponent in grandchildren.children:
                                if not isinstance(datecomponent, lark.Token):
                                    if datecomponent.data == "date":
                                        if len(datetext) > 0:
                                            datetext += ";"
                                            parseddate += ";"
                                        datetext += str(datecomponent.children[0])
                                        ## TODO: parse date further
                                        if datecomponent.children[0].type == "ROMANDATE":
                                            parseddate += parseromandate(str(datecomponent.children[0]), sep=r".,-")
                                elif datecomponent.type == "date":
                                    if len(datetext) > 0:
                                        datetext += ";"
                                        parseddate += ";"
                                    datetext += str(datecomponent.children[0])
                                    if datecomponent.children[0].type == "ROMANDATE":
                                        parseddate += parseromandate(str(datecomponent.children[0]), sep=r".,-")

                        elif grandchildren.data == "locality":
                            if len(locality) > 0:
                                locality += ";"
                            locality += str(grandchildren.children[0])
                        elif grandchildren.data == "other":
                            if len(other) > 0:
                                other += ";"
                            other += str(grandchildren.children[0])
                        elif grandchildren.data == "mixed":
                            for mixedcomponent in grandchildren.children:
                                if not isinstance(mixedcomponent, lark.Token):
                                    if mixedcomponent.data == "leg":
                                        collector = str(mixedcomponent.children[1].children[0])
                                    elif mixedcomponent.data == "det":
                                        determiner = str(mixedcomponent.children[1].children[0])
                                    elif mixedcomponent.data == "legdet":
                                        collector = str(mixedcomponent.children[1].children[0])
                                        determiner = collector
                                    elif mixedcomponent.data == "locality":
                                        if len(locality) > 0:
                                            locality += ";"
                                        locality += str(mixedcomponent.children[0])
                                    elif mixedcomponent.data == "date_string":
                                        for datecomponent in mixedcomponent.children:
                                            if not isinstance(datecomponent, lark.Token):
                                                if datecomponent.data == "date":
                                                    if len(datetext) > 0:
                                                        datetext += ";"
                                                        parseddate += ";"
                                                    datetext += str(datecomponent.children[0])









    # Clean up the genus name
    family = family.lower().capitalize()
    #genus = letters_only(genus)
    genus = genus.lower().capitalize()

    # check taxonomic full name
    ocr_taxonname = " ".join([genus, species, author_name])
    checked_gbif_taxonname = checker.check_full_name(" ".join([genus, species]))

    record = pd.DataFrame({
        "Alt Cat Number": [alt_cat_number],
        "Other Remarks": [other],
        "Family": [family],
        "Genus": [genus],
        "Species": [species],
        "Subspecies": [subspecies],
        "Author name": [author_name],
        "Scientific name": [ocr_taxonname],
        "GBIF checked scientific name": [checked_gbif_taxonname],
        "Determiner": [determiner],
        "Collector": [collector],
        "Number": [col_number],
        "Locality": [locality],
        "Date": [datetext],
        "Parsed date": [parseddate],
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

    family = Path(imgfilename).stem # Assume that the family name is the filename
    #df = parsetext(ocrtext, family, checker)
    df = larkparsetext(ocrtext, family, checker)

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

    #df["Attachment"].update(pd.Series([outfilename], index=[0]))  # Add filename to data record
    df.at[0, "Attachment"] = outfilename  # Add filename to data record

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
    #ocrreader = tesseract.OCR(args["tesseract"], args["language"], config='--oem 3 --psm 6')

    # Initialize taxon checker
    checker = gbiftaxonchecker.GBIFTaxonChecker()

    master_table = empty_dataframe()

    # Loop over a directory of images
    no_img = 0 # Count number of images
    no_pages = 0 # Count number of pages
    for imgfilename in args["image"]:
        print("Transcribing " + imgfilename)
        no_img += 1
        # Check if it is a pdf file
        if Path(imgfilename).suffix == '.pdf':
            print("Reading pages in a pdf file in " + str(args["resolution"]) + " DPI")
            with Image(filename=imgfilename, resolution=args["resolution"]) as img_wand_all:
                no_pages = 0
                # Read all pages
                for img_wand in img_wand_all.sequence:
                    img = np.array(img_wand)
                    no_pages += 1
                    print("Reading page " + str(no_pages))
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
