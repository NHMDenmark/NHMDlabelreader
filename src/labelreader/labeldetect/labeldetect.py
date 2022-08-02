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
from skimage.morphology import disk, closing
import skimage.measure # Needed for label function
from skimage.segmentation import find_boundaries
from skimage.transform import hough_lines, hough_line_peaks
from skimage.feature import corner_fast, corner_peaks


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
        
    # TODO: Maybe check the value channel is large enough to avoid noise from black areas.
    low = img_hsv[:, :, 0] >= huerange[0]
    high = img_hsv[:, :, 0] <= huerange[1]
    
    mask = np.ones(img.shape[0:2], dtype=np.uint8)
    mask[np.logical_and(low, high)] = 0  # Set all background pixels to zero
    
    return mask
    
    
def improve_binary_mask(mask, radius=10, border_margin = 50):
    """Close holes in a binary mask by applying mathematical morphology.
    
       Parameters:
         mask: Binary ndarray (N,M) containing the mask.
         radius: Radius (in integer pixels) of the disk structuring element used for processing.
         border_margin: Border margin in pixels to set to zero (i.e. discard from the mask).
       Returns:
         Binary ndarray (N,M) containing the processed mask
    """

    # Remove any pixels at the border
    mask[0:border_margin, :] = 0
    mask[-border_margin:, :] = 0
    mask[:, 0:border_margin] = 0
    mask[:, -border_margin:] = 0

    selem = disk(radius)
    new_mask = closing(mask, footprint=selem)
    return new_mask


def find_labels(mask):
    """Find all distinct labels from a binary segmentation mask.
       
       Parameters:
         mask: Binary ndarray (N,M) containing the mask
       Returns:
         (label_img, num_labels): Returns a tuple containing labelled image and number of unique labels.
    """
    label_img, num_labels = skimage.measure.label(mask, background=0, return_num=True)
    return label_img, num_labels

    
def resample_label(img, label_img, num_labels):
    """Crop and rotate the label image to be axis aligned by resampling the label pixels.
    
       Parameters:
         img: Image to process as a ndarray in either grayscale or RGB format.
         label_img: Connected compomnents image with unique label identifier as ndarray
                    with dtype=np.int64.
         num_labels: Number of distinct labels found in label_img
       Returns:
         a list of numpy arrays with same number of channels as img which contain the resampled labels.
    """

    lst_resampled_labels = []
    # Loop through all labels ignoring the background segment
    for label in range(1:num_labels+1):
        tmp_label_img = np.zeros_like(label_img)
        bidx = label_img==label
        tmp_label_img[bidx] = label_img[bidx]

        # TODO: Not done - this is slow, consider using a corner detector
        # corner_fast does not work, maybe because I need to convert the image to float representation
        boundaries = find_boundaries(tmp_label_img, mode='outer', background=0)
        boundaries_mask = =np.asarray(boundaries, dtype=np.uint8)
        h, theta, d = hough_lines(boundaries_mask)

    # TODO: This is temporary notes code
    boundaries = find_boundaries(label_img, mode='outer', background=0)
    boundaries_mask = =np.asarray(boundaries, dtype=np.uint8)
    h, theta, d = hough_lines(boundaries_mask)
    for _, angle, dist in zip(*hough_line_peaks(h, theta, d, threshold=np.max(h) * 0.15)):
        (x0, y0) = dist * np.array([np.cos(angle), np.sin(angle)])
        axes.axline((x0, y0), slope=np.tan(angle + np.pi / 2))
    
    # skimage.transform.rotate or even better skimage.transform.estimate_transform
    
    return lst_resampled_labels
    
