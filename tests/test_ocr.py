import pytest
from pathlib import Path
from ocr import tesseract
import pytesseract
import pandas as pd


TESTDATAPATH = Path(__file__).parent
TESSERACT_CMD_PATH = '/opt/local/bin'


def test_ocr_tesseract_init():
    
    ocrreader = tesseract.OCR(TESSERACT_CMD_PATH, 'dan+eng')
    # Check that parameters are set correctly
    #assert ocrreader._tesseract_cmd == '/opt/local/bin'
    assert pytesseract.tesseract_cmd == TESSERACT_CMD_PATH
    assert ocrreader._language == 'dan+eng'
    
    
def test_ocr_tesseract_read_image():
    ocrreader = tesseract.OCR(TESSERACT_CMD_PATH, 'dan+eng')
    
    # Check for empty content
    assert ocrreader.ocr_result == None
    
    ocrreader.read_image(str(TESTDATAPATH.joinpath('scan_lsq523_2022-05-06-15-58-40.png')))
    
    # Check that we now have some content
    assert not isinstance(ocrreader.ocr_result, type(None))
    


def test_ocr_tesseract_get_text():
    ocrreader = tesseract.OCR(TESSERACT_CMD_PATH, 'dan+eng')
    
    ocrreader.read_image(str(TESTDATAPATH.joinpath('scan_lsq523_2022-05-06-15-58-40.png')))
    
    ocrlist = ocrreader.get_text()
    
    # Check that we read some text
    assert len(ocrlist) == 15 # we expect 15 lines of text
    
    # Check the content of the first element in the first sentence
    assert ocrlist[0][0] == '001195'
    
    
def test_ocr_tesseract_get_dataframe():
    ocrreader = tesseract.OCR(TESSERACT_CMD_PATH, 'dan+eng')
    assert ocrreader.get_dataframe() == None
    ocrreader.read_image(str(TESTDATAPATH.joinpath('scan_lsq523_2022-05-06-15-58-40.png')))
    
    assert isinstance(ocrreader.get_dataframe(), pd.core.frame.DataFrame)
    
    
