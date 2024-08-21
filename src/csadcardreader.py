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
import pandas as pd
import re
from pathlib import Path
from wand.image import Image
import numpy as np
import lark
import datetime

# Adding path to ocr package - this can probably be done smarter
# from pathlib import Path
# print("Adding to syspath: " + str(Path(__file__).parent.parent))
# sys.path.append(str(Path(__file__).parent.parent))

from labelreader.ocr import tesseract
from labelreader.util.util import checkfilepath
from labelreader.taxonchecker import gbiftaxonchecker
from labelreader.util.util import parseromandate


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
        "Parsed date DD-MM-YYYY": [],
        "Date range": [],
        "Attachment": []
    })
    return record


def isvaliddate(datestr: str) -> bool:
    """Return True if the date string is not in the future.

        datestr: String with the date to check in the format DD-MM-YYYY
        Return: Boolean
    """
    try:
        # Check that day and month are non-zero
        parts = re.split("[-]", datestr)
        if int(parts[0]) == 0:
            day = 1
        else:
            day = int(parts[0])

        if int(parts[1]) == 0:
            month = 1
        else:
            month = int(parts[1])
        parsed_date = "%02d" % day + "-" + "%02d" % month + "-" + parts[2]
        date = datetime.datetime.strptime(parsed_date,"%d-%m-%Y").date()
        today = datetime.date.today()
        if date < today:
            return True
        else:
            return False
    except ValueError:
        return False


def clean_catalogue_number(text: str) -> str:
    """Clean the text and return a version with digits, '.' and '-'.

        text: String to clean
        Return: A cleaned string
    """
    cleantext = re.sub(r"[ .,]{1,2}", '.', text)
    cleantext = re.sub(r"[-—~]+", '-', cleantext)
    cleantext = re.sub(r"l", '1', cleantext)
    cleantext = re.sub(r"o", '0', cleantext)
    return cleantext



class CSADVisitor(lark.Visitor):
    def  __init__(self):
        super().__init__()
        self.data = {}

    # top_line methods
    def family(self, tree):
        if "family" in self.data:
            self.data["family"] += ";" + str(tree.children[0])
        else:
            self.data["family"] = str(tree.children[0])

    def catcode(self, tree):
        self.data["catcode"] = str(tree.children[0])

    def catnumber(self, tree):
        self.data["catnumber"] = clean_catalogue_number(str(tree.children[0]))

    # nodot methods
    def nodot(self, tree):
        if "nodot" in self.data:
            self.data["nodot"] += ";" + str(tree.children[0])
        else:
            self.data["nodot"] = str(tree.children[0])

    # taxon_lines methods
    def genus(self, tree):
        if "genus" in self.data:
            self.data["genus"] += " " + str(tree.children[0])
        else:
            self.data["genus"] = str(tree.children[0])

    def species(self, tree):
        if "species" in self.data:
            self.data["species"] += " " + str(tree.children[0])
        else:
            self.data["species"] = str(tree.children[0])

    def subspecies(self, tree):
        if "subspecies" in self.data:
            self.data["subspecies"] += " " + str(tree.children[0])
        else:
            self.data["subspecies"] = str(tree.children[0])

    def author(self, tree):
        if "author" in self.data:
            self.data["author"] += " " + str(tree.children[0])
        else:
            self.data["author"] = str(tree.children[0])

    # leg and det methods
    def leg(self, tree):
        if "leg" in self.data:
            self.data["leg"] += ";" + str(tree.children[1].children[0])
        else:
            self.data["leg"] = str(tree.children[1].children[0])

    def det(self, tree):
        if "det" in self.data:
            self.data["det"] += ";" + str(tree.children[1].children[0])
        else:
            self.data["det"] = str(tree.children[1].children[0])

    def legdet(self, tree):
        if "leg" in self.data:
            self.data["leg"] += ";" + str(tree.children[1].children[0])
        else:
            self.data["leg"] = str(tree.children[1].children[0])
        if "det" in self.data:
            self.data["det"] += ";" + str(tree.children[1].children[0])
        else:
            self.data["det"] = str(tree.children[1].children[0])

    # locality and other methods
    def locality(self, tree):
        if "locality" in self.data:
            self.data["locality"] += ";" + str(tree.children[0])
        else:
            self.data["locality"] = str(tree.children[0])

    def other(self, tree):
        if "other" in self.data:
            self.data["other"] += ";" + str(tree.children[0])
        else:
            self.data["other"] = str(tree.children[0])

    # date methods
    def daterange(self, tree):
        if "daterange" in self.data:
            self.data["daterange"] += ";" + str(tree.children[0])
        else:
            self.data["daterange"] = str(tree.children[0])

    def romandate(self, tree):
        date = str(tree.children[0])
        if "date" in self.data:
            self.data["date"] += ";" + date
        else:
            self.data["date"] = date

        # Remove OCR errors
        date = re.sub(r"[ \.,…\-/]+", "-", date)

        parsed_date  = parseromandate(date, sep=r"-")
        if "parsed_date" in self.data:
            self.data["parsed_date"] += ";" + parsed_date
        else:
            self.data["parsed_date"] = parsed_date

    def year(self, tree):
        year = str(tree.children[0])
        parsed_date = "00-00-" + year

        if isvaliddate(parsed_date):
            if "date" in self.data:
                self.data["date"] += ";" + year
            else:
                self.data["date"] = year

            if "parsed_date" in self.data:
                self.data["parsed_date"] += ";" + parsed_date
            else:
                self.data["parsed_date"] = parsed_date
        else:
            if "other" in self.data:
                self.data["other"] += ";" + year
            else:
                self.data["other"] = year


    def dmydate(self, tree):
        date = str(tree.children[0])
        if "date" in self.data:
            self.data["date"] += ";" + date
        else:
            self.data["date"] = date

        # Split into Day, Month, Year parts
        parts = re.split(r"[ .,/-]{1}", date)
        if len(parts) == 3:
            day = parts[0]
            month = parts[1]
            year = parts[2]
        else:
            day = "00"
            month = "00"
            year = "0000"

        try:
            parsed_date = "%02d" % int(day) + "-" + "%02d" % int(month) + "-" + "%04d" % int(year)
        except ValueError:
            parsed_date = ""

        if "parsed_date" in self.data:
            self.data["parsed_date"] += ";" + parsed_date
        else:
            self.data["parsed_date"] = parsed_date


    def monthnamedate(self, tree):
        date = ""
        day = ""
        if len(tree.children) == 3:
            day = str(tree.children[0])

        month = str(tree.children[-2])
        year = str(tree.children[-1])

        if len(day) != 0:
            date += day + " "
        if len(month) != 0:
            date += month + " "
        date += year

        if "date" in self.data:
            self.data["date"] += ";" + date
        else:
            self.data["date"] = date

        # Parse the month name
        month_map = {"januar": "01", "january": "01",  "jan": "01",
                     "februar": "02", "february": "02", "feb": "02",
                     "marts": "03", "march": "03", "mar": "03",
                     "april": "04",
                     "maj": "05", "may": "05",
                     "juni": "06", "june": "06",
                     "juli": "07", "july": "07",
                     "august": "08", "aug": "08",
                     "september": "09", "sep": "09",
                     "oktober": "10", "october": "10", "okt": "10", "oct": "10",
                     "november": "11", "nov": "11",
                     "december": "12", "dec": "12"
                     }

        month = re.sub(r"[.,]", "", month).lower()
        if month in month_map:
            month_num = month_map[month]
        else:
            month_num = "00"

        try:
            parsed_date = ""
            if len(day) != 0:
                parsed_date += "%02d" % int(day) + "-"
            else:
                parsed_date += "00-"
            parsed_date += month_num + "-" + "%04d" % int(year)
        except ValueError:
            parsed_date = ""

        if "parsed_date" in self.data:
            self.data["parsed_date"] += ";" + parsed_date
        else:
            self.data["parsed_date"] = parsed_date




def larkparsetext(ocrtext: str, family: str, checker: str, args: dict) -> pd.DataFrame:
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
    ocr_taxonname = " "
    checked_gbif_taxonname = " "
    determiner = ""
    collector = ""
    col_number = ""
    locality = ""
    datetext = ""
    parseddate = ""
    daterange = ""



    # Read the grammar and create the parser
    gf = open("../grammars/csad.lark", "r")
    grammar = gf.read()
    parser = lark.Lark(grammar, start='card')

    # Create a text string from the list of lists from the OCR
    text = ""
    for idx in range(0, len(ocrtext)):
        text += " ".join(ocrtext[idx]) + "\n"

    try:
        # Create the parse tree
        ptree = parser.parse(text)

        # Process the parse tree
        visitor  = CSADVisitor()
        visitor.visit(ptree)
        if args["verbose"]:
            print(visitor.data)

        # Extract the data from the visitor
        # TODO: Check if the data is present before assigning it to the variables
        if "catcode" in visitor.data:
            alt_cat_number += visitor.data["catcode"]
        if "catnumber" in visitor.data:
            alt_cat_number += visitor.data["catnumber"]
        if "family" in visitor.data:
            family = visitor.data["family"].lower().capitalize()
        if "genus" in visitor.data:
            genus = visitor.data["genus"].lower().capitalize()
        if "species" in visitor.data:
            species = visitor.data["species"].lower()
        if "subspecies" in visitor.data:
            subspecies = visitor.data["subspecies"]
        if "author" in visitor.data:
            author_name = visitor.data["author"]
        if "leg" in visitor.data:
            collector = visitor.data["leg"]
        if "det" in visitor.data:
            determiner = visitor.data["det"]
        if "nodot" in visitor.data:
            col_number = visitor.data["nodot"]
        if "locality" in visitor.data:
            locality = visitor.data["locality"]
        if "other" in visitor.data:
            other = visitor.data["other"]
        if "date" in visitor.data:
            datetext = visitor.data["date"]
        if "parsed_date" in visitor.data:
            parseddate = visitor.data["parsed_date"]
        if "daterange" in visitor.data:
            daterange = visitor.data["daterange"]

        # check taxonomic full name
        ocr_taxonname = " ".join([genus, species, author_name])
        checked_gbif_taxonname = checker.check_full_name(" ".join([genus, species]))
    except lark.UnexpectedInput as e:
        print("Error in parsing:")
        print(e.get_context(text))

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
        "Parsed date DD-MM-YYYY": [parseddate],
        "Date range": [daterange],
        "Attachment": [""]
    })

    return record


def process_image(img, imgfilename, no_img, no_pages, args, ocrreader, master_table, checker):
    """Parse one image and create a row in the master_table"""

    ocrreader.read_image(img)

    ocrtext = ocrreader.get_text()

    if args["verbose"]:
        for i in range(len(ocrtext)):
            print(ocrtext[i])

    family = Path(imgfilename).stem # Assume that the family name is the filename
    df = larkparsetext(ocrtext, family, checker, args)

    #  In case of no Alt Cat Number just pick a unique random file name
    if df["Alt Cat Number"][0] == "":
        outfilename = Path(imgfilename).stem + "_image" + str(no_img) + "_page" + str(no_pages) + ".tif"
    else:
        outfilename = df["Alt Cat Number"][0] + ".tif"

    # Check that filename is unique otherwise create an extension of it to make unique
    outpath = Path(args["output"], Path(imgfilename).stem)
    outfilepath = Path(outpath, outfilename)
    outfilepath = checkfilepath(outfilepath)
    outfilename = outfilepath.name

    imsave(str(outfilepath), img, check_contrast=False, plugin='pil', compression="tiff_lzw",
           resolution_unit=2, resolution=args["resolution"])

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
    outfilepath = Path(args["output"], "output.xlsx")
    for imgfilename in args["image"]:
        print("Transcribing " + imgfilename)
        no_img += 1
        # Check if it is a pdf file
        if Path(imgfilename).suffix == '.pdf':
            print("Reading pages in a pdf file in " + str(args["resolution"]) + " DPI")
            # Make sure output directory exists
            outpath = Path(args["output"], Path(imgfilename).stem)
            outfilepath = Path(outpath, Path(imgfilename).stem + ".xlsx")
            if not outpath.exists():
                outpath.mkdir()

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

        # Write Excel sheet to disk
        master_table.to_excel(outfilepath.as_posix(), index=False)
        master_table = empty_dataframe()


if __name__ == '__main__':
    main()
