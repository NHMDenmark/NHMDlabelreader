import pytest
import sys
from skimage.io import imread
import numpy as np

from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.joinpath('src')))

from labelreader.labeldetect import labeldetect

TESTDATAPATH = Path(__file__).parent

def test_color_segment_labels():
    # TODO: Use a smaller image for testing than this one
    #img = imread(str(TESTDATAPATH.joinpath('JPG_400DPI.jpg')))

    # Construct a 5 color stripped pattern test image
    red = np.array([1.0, 0.0, 0.0], dtype=float)
    green = np.array([0.0, 1.0, 0.0], dtype=float)
    blue = np.array([0.0, 0.0, 1.0], dtype=float)
    black = np.array([0.0, 0.0, 0.0], dtype=float)
    white = np.array([1.0, 1.0, 1.0], dtype=float)
    img = np.zeros((10, 50, 3))
    img[:, 0:10] = black
    img[:, 10:20] = red
    img[:, 20:30] = green
    img[:, 30:40] = blue
    img[:, 40:50] = white


    # test default settings
    segMask = labeldetect.color_segment_labels(img) # Red background
    
    # Check that the returned image is of the same shape
    assert img.shape[0:2] == segMask.shape
    assert segMask.dtype == np.uint8
    assert np.count_nonzero(segMask) == 400 # Check amount of foreground pixels - red background

    # Test different colors
    segMask = labeldetect.color_segment_labels(img, huerange=(0.32,0.37)) # Green background
    assert np.count_nonzero(segMask) == 400  # Check amount of foreground pixels - green background

    segMask = labeldetect.color_segment_labels(img, huerange=(0.63, 0.68)) # Blue background
    assert np.count_nonzero(segMask) == 400  # Check amount of foreground pixels - green background


def maketestlabelimg():
    """Construct an image with four 100x100 pixel white squares on a red background"""
    img = np.zeros((500, 500, 3))
    red = np.array([1.0, 0.0, 0.0], dtype=float)
    white = np.array([1.0, 1.0, 1.0], dtype=float)
    img[:, :, :] = red
    img[100:200, 100:200] = white
    img[100:200, 300:400] = white
    img[300:400, 100:200] = white
    img[300:400, 300:400] = white
    return img


def test_improve_binary_mask():
    img = maketestlabelimg()
    segMask = labeldetect.color_segment_labels(img)

    assert np.count_nonzero(segMask) == 4 * 10000  # pixels

    segMask[10:20, 10:20]=1 # Add a 10x10 pixel square of ones that we want to remove

    segMask2 = labeldetect.improve_binary_mask(segMask)
    
    # Check that the returned image is of the same shape
    assert segMask.shape == segMask2.shape
    assert segMask.dtype == segMask2.dtype
    assert np.count_nonzero(segMask2) == 4 * 10000  # pixels

    
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
