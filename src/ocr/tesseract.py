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

import pytesseract
import pandas as pd
import cv2



class OCR():
    """This class is a wrapper data structure on the tesseract and pytesseract OCR library.
    """
    
    def __init__(self, tesseract_cmd, language):
        """        
        tesseract_cmd - must be set to the path to the tesseract executable
        language - String setting the language to use by tesseract. Multi-languages can be defined as e.g. 'eng+dan' """
        self._tesseract_cmd = tesseract_cmd
        pytesseract.tesseract_cmd = self._tesseract_cmd
        self._language = language
        self.ocr_result = None
    
    
    def read_image(self, image):
        """Parses the image and populates the internal data structures of this class.
        The image must be a numpy array in RGB color channel order."""
        self.image = image
        self.ocr_result = pytesseract.image_to_data(image, lang=self._language, output_type=pytesseract.Output.DATAFRAME)
        
        
    def get_text(self):
        """Returns a list of strings with the text read from the image. 
        
        Remember to call read_image before calling this method."""
        retlist = []
        if isinstance(self.ocr_result, type(None)):
            print("Warning: You must call read_image prior to calling the get_text method!")
        else:
            #linenum = 0
            linetext = []
            # Make a sentence of read symbols for each line read in the image
            for index, row in self.ocr_result.iterrows():
                if row['conf'] > 0 and row['width'] * row['height'] > 20: # Check confidence value and that the box has area larger than 10 pixels^2
                    if row['word_num'] == 1:
                        if len(linetext) != 0:
                            retlist.append(linetext)
                            
                        linetext = []
                        
                    linetext.append(row['text'])
            
            if len(linetext) != 0:
                retlist.append(linetext)
                    
        return retlist
        
        
    def get_dataframe(self):
        """Return the result from tesseract as a Pandas dataframe. 
        Returns None if is read_image has not been called."""
        return self.ocr_result


    def visualize_boxes(self):
        """Visualize the blocks of text detected by tesseract.
        
        Remember to call read_image before calling this method.
        """
        colors = [(0, 0, 0), # Color rectangle lines
                  (0, 0, 255),
                  (0, 64, 255),
                  (0, 191, 255),
                  (0, 255, 0),
                  (255, 0, 0),
                  (255, 64, 0),
                  (255, 191, 0),
                  (0, 255, 255),
                  (255, 255, 0),
                  (255, 0, 255)
                ]
        line_thickness = 3 # pts

        img = cv2.imread(self.image)
        
        if isinstance(self.ocr_result, type(None)):
            print("Warning: You must call read_image prior to calling the get_text method!")
        else:
            for index, row in self.ocr_result.iterrows():
                if row['conf'] > 0 and row['width'] * row['height'] > 20: # Check confidence value and that the box has area larger than 10 pixels^2
                    top_coord = (row['left'], row['top']) # left, top
                    bottom_coord = (row['left'] + row['width'], row['top'] + row['height']) # left + width, top + height
                    colidx = row['block_num'] % len(colors) # Cyclic use of colors if we block_num is larger than the allocated colors.                        
                    cv2.rectangle(img, top_coord, bottom_coord, colors[colidx], line_thickness)
        
        cv2.namedWindow("Boxes")
        cv2.imshow("Boxes", img)
        cv2.waitKey()
