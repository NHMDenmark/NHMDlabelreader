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

import argparse
import cv2
import pytesseract
import zxingcpp
import pprint
#from pyzbar import pyzbar
#from pyzbar.pyzbar import ZBarSymbol
#import pylibdmtx.pylibdmtx as dmtx

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-t", "--tesseract", required=True,
                help="path to tesseract executable")
ap.add_argument("-i", "--image", required=True,
                help="file name for and path to input image")
ap.add_argument("-l", "--language", required=False, default="eng",
                help="language that tesseract uses - depends on installed tesseract language packages")
ap.add_argument("-c", "--codeformat", required=False, default='none', choices=['dmtx', 'qr', 'none'],
                help="choose between searching for QR code (qr) or Data Matrix code (dmtx). Default=none - no search.")
args = vars(ap.parse_args())

print("Using language = " + args["language"] + "\n")


# Create OCR Tesseract object
pytesseract.tesseract_cmd = args["tesseract"]


# Read an image
img = cv2.imread(args["image"])
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

if args["codeformat"] == 'qr':
    # Find the QR codes in the image and decode each of the barcodes
    # Inspired by https://www.pyimagesearch.com/2018/05/21/an-opencv-barcode-and-qr-code-scanner-with-zbar/
    # pyzbar is developed by NHM London, https://github.com/NaturalHistoryMuseum/pyzbar

    height, width = img_gray.shape[:2]
    #qrcodes = pyzbar.decode((img_gray.tobytes(), width, height), symbols=[ZBarSymbol.QRCODE])
    qrcodes = zxingcpp.read_barcodes(img_gray, formats=zxingcpp.QRCode)

    print("QR codes:\n")
    print(qrcodes)

elif args["codeformat"] == 'dmtx':
    # Find Data Matrix codes in the image and decode
    # https://github.com/NaturalHistoryMuseum/pylibdmtx/ as maintained by NHM London
    # REALLY SLOW - must detect code area and do a cropping of the image before calling decode
    #dmcodes = dmtx.decode(img_rgb)

    # Much faster
    dmcodes = zxingcpp.read_barcodes(img, formats=zxingcpp.DataMatrix)
    #dmcodes = zxingcpp.read_barcode(img)

    print("Data Matrix codes:\n")
    for dmcode in dmcodes:
        print(
            "Found barcode:"
            f'\n Text:    "{dmcode.text}"'
            f"\n Format:   {dmcode.format}"
            f"\n Content:  {dmcode.content_type}"
            f"\n Position: {dmcode.position}"
            f"\n Orientation: {dmcode.orientation}"
        )


# Run it through the OCR engine
# See https://github.com/madmaze/pytesseract
print("\n OCR read text:\n")
print(pytesseract.image_to_string(img_rgb, lang=args["language"]))

# ocr_result = pytesseract.image_to_data(img_rgb, lang=args["language"])
# ocr_boxes = pytesseract.image_to_boxes(img_rgb, lang=args["language"])
