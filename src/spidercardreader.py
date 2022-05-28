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

import sys
import argparse
import cv2
import pandas as pd

# Adding path to ocr package - this can probably be done smarter
#from pathlib import Path
#print("Adding to syspath: " + str(Path(__file__).parent.parent))
#sys.path.append(str(Path(__file__).parent.parent))

from labelreader.ocr import tesseract


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

    ocrreader = tesseract.OCR(args["tesseract"], args["language"])

    ocrreader.read_image(args["image"])

    ocrtext = ocrreader.get_text()
    for i in range(len(ocrtext)):
        print(ocrtext[i])

    ocrreader.visualize_boxes()



if __name__ == '__main__':
    main()
