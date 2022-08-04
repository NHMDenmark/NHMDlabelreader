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
import math
from skimage.color import rgb2hsv
from skimage.morphology import disk, closing, opening
import skimage.measure  # Needed for label function and regionprop
from skimage.transform import EuclideanTransform, warp

def color_segment_labels(img, huerange=(0.0, 0.05)):
    """Perform a simple color-based foreground-background segmentation to find all labels in an image.
       The segmentation is perfomed by converting the image to HSV color space representation and then 
       perform a range threshold on the hue channel. It is assumed that the background is neither black
       nor white. Remember that hue is periodic (in the range [0, 1]) and the thresholding is always
       performed on shortest interval.
    
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
    notblack = img_hsv[:, :, 2] > 0.01
    notwhite = img_hsv[:, :, 1] > 0.01
    
    mask = np.ones(img.shape[0:2], dtype=np.uint8)
    mask[np.logical_and(np.logical_and(np.logical_and(low, high), notwhite), notblack)] = 0  # Set all background pixels to zero
    
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
    new_mask = opening(mask, footprint=selem)
    #selem_big = disk(2*radius)
    #new_mask = closing(new_mask, footprint=selem_big)
    new_mask = closing(new_mask, footprint=selem)
    return new_mask


def find_labels(mask):
    """Find all distinct labels from a binary segmentation mask and label pixels belonging to
       each distinct label with a unique label number.
       
       Parameters:
         mask: Binary ndarray (N,M) containing the mask
       Returns:
         (label_img, num_labels): Returns a tuple containing labelled image and number of unique labels.
    """
    label_img, num_labels = skimage.measure.label(mask, background=0, return_num=True)
    return label_img, num_labels

    
def resample_label(img, label_img, num_labels):
    """Crop and rotate the label image to be axis aligned by resampling the label pixels.
        We assume that labels in images are rectangular, but can be oriented in anyway in the image.
    
       Parameters:
         img: Image to process as an ndarray in either grayscale or RGB format.
         label_img: Labelled connected compomnents image with unique label identifier as ndarray
                    with dtype=np.int64.
         num_labels: Number of distinct labels found in label_img
       Returns:
         a list of numpy arrays with same number of channels as img which contain the resampled labels.
    """

    lst_resampled_labels = []

    props = skimage.measure.regionprops(label_img)

    # Loop through all labels ignoring the background segment
    for prop in props:
        label_id = prop.label
        orientation = prop.orientation
        centroid = prop.centroid
        axis_minor_length = prop.axis_minor_length
        axis_major_length = prop.axis_major_length
        bbox = prop.bbox
        area = prop.area


        # Use area and minor/major axis length to check if aspect ratio and aread of region is reasonable
        #  otherwise discard
        if (axis_minor_length / axis_major_length < 0.8) and (area > 1000):
            # Convert centroid from (row,col) to (x,y) representation
            center = -np.array([centroid[1], centroid[0]], dtype=float)

            # Find upper left corner of rotated bounding box
            corner = np.array([0.5 * axis_major_length, 0.5 * axis_minor_length], dtype=float)


            # Construct inverse homogeneous Euclidean transformation matrix to transform
            # label in img into a cropped and axis aligned image of this label
            trans_centroid = np.eye(3, dtype=float)
            trans_centroid[0, 2] = center[0]
            trans_centroid[1, 2] = center[1]
            rotate_crop = EuclideanTransform(rotation=(orientation+np.pi /2.0), translation=corner)

            # Combined transform
            transf = np.dot(rotate_crop.params, trans_centroid)
            # The inverse of the combined transform
            inv_transf = np.linalg.inv(transf)


            # Crop and rotate image
            # TODO: Consider rounding output_shape instead of truncating to integer - Does not seem to be important
            warped = warp(img, inv_transf, output_shape=(int(axis_minor_length), int(axis_major_length)))

            # Add region properties to a dictionary together with image of label
            label_data = dict()  # Create a new empty dictionary object
            label_data['label_id'] = label_id
            label_data['orientation'] = orientation
            label_data['centroid'] = centroid
            label_data['axis_minor_length'] = axis_minor_length
            label_data['axis_major_length'] = axis_major_length
            label_data['bbox'] = bbox
            label_data['area'] = area
            label_data['image'] = warped

            # Append cropped image of label to lst_resampled_labels.
            lst_resampled_labels.append(label_data)

    return lst_resampled_labels
    
