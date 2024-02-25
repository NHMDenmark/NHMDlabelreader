# -*- coding: utf-8 -*-
#  Copyright (c) 2022  Natural History Museum of Denmark (NHMD)
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import pytest
import sys
import pytesseract
import pandas as pd

from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.joinpath('src')))

from labelreader.ocr import tesseract



TESTDATAPATH = Path(__file__).parent
TESSERACT_CMD_PATH = '/opt/local/bin'

def is_tesseract_installed():
    try:
        pytesseract.get_tesseract_version()
        return False
    except pytesseract.pytesseract.TesseractNotFoundError:
        return True

def test_ocr_tesseract_init():
    
    ocrreader = tesseract.OCR(TESSERACT_CMD_PATH, 'dan+eng')
    # Check that parameters are set correctly
    assert pytesseract.tesseract_cmd == TESSERACT_CMD_PATH
    assert ocrreader._language == 'dan+eng'
    # Check for empty content
    assert ocrreader.ocr_result == None

    
@pytest.mark.skipif(is_tesseract_installed(), reason="Tesseract is not installed")
def test_ocr_tesseract_read_image():
    ocrreader = tesseract.OCR(TESSERACT_CMD_PATH, 'dan+eng')

    ocrreader.read_image(str(TESTDATAPATH.joinpath('scan_lsq523_2022-05-06-15-58-40.png')))
    
    # Check that we have some content
    assert not isinstance(ocrreader.ocr_result, type(None))
    

@pytest.mark.skipif(is_tesseract_installed(), reason="Tesseract is not installed")
def test_ocr_tesseract_get_text():
    ocrreader = tesseract.OCR(TESSERACT_CMD_PATH, 'dan+eng')
    
    ocrreader.read_image(str(TESTDATAPATH.joinpath('scan_lsq523_2022-05-06-15-58-40.png')))
    
    ocrlist = ocrreader.get_text()
    
    # Check that we read some text
    assert len(ocrlist) == 15 # we expect 15 lines of text
    
    # Check the content of the first element in the first sentence
    assert ocrlist[0][0] == '001195'
    
@pytest.mark.skipif(is_tesseract_installed(), reason="Tesseract is not installed")
def test_ocr_tesseract_get_dataframe():
    ocrreader = tesseract.OCR(TESSERACT_CMD_PATH, 'dan+eng')
    assert ocrreader.get_dataframe() == None
    ocrreader.read_image(str(TESTDATAPATH.joinpath('scan_lsq523_2022-05-06-15-58-40.png')))
    
    assert isinstance(ocrreader.get_dataframe(), pd.core.frame.DataFrame)
    
    
