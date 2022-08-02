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
    assert segMask.dtype == np.uint8
    

def test_improve_binary_mask():
    # TODO: Use a prepared mask for testing instead of a segmentation of the image
    img = imread(str(TESTDATAPATH.joinpath('JPG_400DPI.jpg')))
    segMask = labeldetect.color_segment_labels(img)
    segMask2 = labeldetect.improve_binary_mask(segMask)
    
    # Check that the returned image is of the same shape
    assert segMask.shape == segMask2.shape
    assert segMask.dtype == segMask2.dtype
    # TODO: Add additional tests that the result is as expected (without testing the underlying library functions)
    
def test_find_labels():
    # TODO: Write this test
    pass

def test_resample_label():
    img = imread(str(TESTDATAPATH.joinpath('JPG_400DPI.jpg')))
    segMask = labeldetect.color_segment_labels(img)
    segMask = labeldetect.improve_binary_mask(segMask)
    label_img, num_labels = labeldetect.find_labels(segMask)
    lst_resampled_labels = labeldetect.resample_label(img, label_img, num_labels)

    assert len(lst_resampled_labels) == 9
