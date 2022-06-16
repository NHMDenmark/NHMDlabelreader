# -*- coding: utf-8 -*-
"""
Created on Thu May 31 16:58:00 2022

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
import numpy as np
from skimage.color import rgb2hsv
from skimage.morphology import binary_dilation, binary_erosion, binary_closing, disk, closing
from skimage.measure import label


def color_segment_labels(img, huerange=(0.0, 0.1)):
    """Perform a simple color-based foreground-background segmentation to find all labels in an image.
       The segmentation is perfomed by converting the image to HSV color space representation and then 
       perform a range threshold on the hue channel. Remember that hue is periodic (in the range [0, 1]) 
       and the thresholding is always performed on shortest interval.
    
       Parameters:
         img: image to be segmented as a ndarray (N,M,C) in either grayscale (C=1) or RGB (C=3) format.
         huerange: a 2-tuple indicating the range of hue values corresponding to background. 
    
       Returns:
         binary segmentation mask as a ndarray (N,M). 
    """
    img_hsv = rgb2hsv(img)
        
    # TODO: Maybe check the value channel is large enough to avoid black noise.
    low = img_hsv[:, :, 0] >= huerange[0]
    high = img_hsv[:, :, 0] <= huerange[1]
    
    mask = np.ones(img.shape[0:2], dtype=np.uint8)
    mask[np.logical_and(low, high)] = 0  # Set all background pixels to zero
    
    return mask
    
    
def improve_binary_mask(mask, radius=10):
    """Close holes in a binary mask by applying mathematical morphology.
    
       Parameters:
         mask: Binary ndarray (N,M) containing the mask
         radius: Radius (in integer pixels) of the disk structuring element used for processing
       Returns:
         Binary ndarray (N,M) containing the processed mask
    """
    selem = disk(radius)
    new_mask = closing(mask, footprint=selem)
    return new_mask


def find_labels(mask):
    """Find all distinct labels from a binary segmentation mask.
       
       Parameters:
         mask: Binary ndarray (N,M) containing the mask
       Returns:
         A list of detected label oriented bounding boxes as 8-tuples containing the four 
         corner coordinates.
    """
    # TODO
    pass
    
    
def resample_label(img, bbox):
    """Crop and rotate the label image to be axis aligned by resampling the label pixels.
    
       Parameters:
         img - image as a ndarray in either grayscale or RGB format.
         bbox - Bounding box of label to be resampled.
       Returns:
         a numpy array with same number of channels as img which contain the resampled label.
    """
    
    # TODO
    
    # skimage.transform.rotate
    
    pass
    
