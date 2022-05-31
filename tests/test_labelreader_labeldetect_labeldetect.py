import pytest
import sys
from skimage.io import imread
import numpy as np

from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.joinpath('src')))

from labelreader.labeldetect import labeldetect

TESTDATAPATH = Path(__file__).parent

def test_color_segment_labels():
    # TODO: Use a smaller image for testing
    img = imread(str(TESTDATAPATH.joinpath('JPG_400DPI.jpg')))
    
    segMask = labeldetect.color_segment_labels(img)
    
    # Check that the returned image is of the same shape
    assert img.shape[0:2] == segMask.shape
    assert isinstance(segMask.dtype, np.uint8) 
    

def test_improve_binary_mask():
    # TODO: Use a prepared mask for testing instead of a segmentation of the image
    img = imread(str(TESTDATAPATH.joinpath('JPG_400DPI.jpg')))
    segMask = labeldetect.color_segment_labels(img)
    segMask2 = labeldetect.improve_binary_mask(segMask)
    
    # Check that the returned image is of the same shape
    assert segMask.shape == segMask2.shape
    assert segMask.dtype == segMask2.dtype 
    
