#! /bin/env python

import sys, os
import PIL
import numpy as np
from scipy import ndimage, misc
from copy import copy
from matplotlib.pyplot import plot, show


# Module to compute the area of an irregulare, closed, convex polygon.
# The x and y vectors are the vertices ; the last should equal the first
def poly_area(x,y):
    area = 0.0
    nx = len(x)
    for i,x_i in enumerate(x):
        if (i == nx-1): break
        area += (x_i*y[i+1] - x[i+1]*y[i])*0.5

    return abs(area)


# Module to compute chain code of a feature's contour 
# (represented by its pixel value) on a image.
# Inputs:
#       image       - 2d numpy array
#       pixel_value - scalar containing the pixel value
#                     of feature on the image.
# Outputs:
#       chaincode, locations - String containing the chain code
#                              of the feature's contour,
#                              and locations [X,Y] of the contour's pixels
#
def image2chain(image,pixel_value,
                FILL_HOLES=False,
                REMOVE_ISOLATED_PIXELS=False,
                VERBOSE=True):

    ardir = np.array([[-1,0],[-1,1],[0,1],[1,1],[1,0],[1,-1],[0,-1],[-1,-1]])
    ccdir = np.array([0,7,6,5,4,3,2,1])
    
    if (image.ndim != 2):
        print ("Error: input array must have 2 dimensions!")
        return "",[]

    nX = image.shape[0] ; nY = image.shape[1]
    n = nX*nY
    mask = (image == pixel_value)

    if (REMOVE_ISOLATED_PIXELS): mask = closerec(mask)
    if (FILL_HOLES): mask = fill_holes(mask)

    # Find location of the starting pixel [X,Y]
    # It must be the leftmost-uppermost pixel belonging to the feature
    indices = np.where(mask)
    cc_x_pix = min(indices[0])
    cc_y_pix = max(indices[1][np.where(indices[0] == cc_x_pix)])

    chaincode="" ; locations = []
    xpix = int(cc_x_pix) ; ypix = int(cc_y_pix)
    loop = True ; niter=0
    while (loop):
        for i,direction in enumerate(ardir):
            x = xpix + direction[0] ; y = ypix + direction[1]
            current_ccdir = ccdir[i]
            if (mask[x,y]): break
        chaincode += str(current_ccdir)
        locations.append([xpix,ypix]) 
        # if return to starting pixel, then stop
        if ([x,y] == [cc_x_pix,cc_y_pix]): 
            locations.append([x,y])
            loop=False
        # assign new pixel position
        xpix = x ; ypix = y
        # rotate direction vector
        ishift = int(np.where(ccdir == (int(current_ccdir)+4)%8)[0])
        ardir = np.roll(ardir,7-ishift,axis=0) ; ccdir = np.roll(ccdir,7-ishift)
        niter+=1
        if (niter > n): 
            if (VERBOSE): print ("Error: can not compute chain code!")
            return "",[]
    
    return chaincode, locations

# Module to compute a feature's contour on a image from its chain code.
# Inputs:
#       chain       - string containing the chain code
#       start_pixel - location [X,Y] of the starting pixel.
#
# Outputs:
#       locations - the locations X and Y of the feature's contour.
#
def chain2image(chain,start_pixel=[0,0],
                VERBOSE=True,CCLOCKWISE=False):

    pix0 = np.array(start_pixel)
    ardir = np.array([[-1,0],[-1,1],[0,1],[1,1],[1,0],[1,-1],[0,-1],[-1,-1]])
    ccdir = np.array([0,7,6,5,4,3,2,1])
    if (CCLOCKWISE):ardir[:,1] = -ardir[:,1]
    

    X = [pix0[0]] ; Y = [pix0[1]]
    for direction in chain:
        X.append(np.int64(X[-1]) + ardir[int(direction)][0])
        Y.append(np.int64(Y[-1]) + ardir[int(direction)][1])
        
    return X,Y

# Module to apply a closing reconstruction operator on the input binary image
def closerec(image,open_structure=None,close_structure=None):

    # Multiple erosion operations
    if not (isinstance(image[0,0],np.bool_)):
        binary_image = image > 0
    else:
        binary_image = image.copy()
    
    current_image1 = binary_image.copy()
    while (True in current_image1):
        current_image0 = current_image1.copy()
        current_image1 = ndimage.morphology.binary_erosion(current_image0,
                                              structure=open_structure)
            
    # Multiple dilatation operations
    reconstruct_image = ndimage.morphology.binary_propagation(
        current_image0,structure=close_structure,mask=binary_image)
        
    return reconstruct_image

# Apply ndimage.morphology.fill_holes module on the input binary image
def fill_holes(image,structure=None):
  
    # Multiple erosion operations
    if not (isinstance(image[0,0],np.bool_)):
        binary_image = image > 0
    else:
        binary_image = image.copy()
  
    filled_image = ndimage.morphology.binary_fill_holes(binary_image,
                                                        structure=structure)
    return filled_image

# Module to adjust automatically the contrast of an image using
# the histogram of its pixel's values.
def auto_contrast(image,low=0.02,high=0.99):

    max_val = np.max(image)
    min_val = np.min(image)
    imb = misc.bytescale(image)
    xh = np.array(range(257))
    histo = np.histogram(imb,bins=xh)
    xh = histo[1][0:-1]
    yh = histo[0]
    #    plot(xh,yh)
    #    show()
    yhtot = np.sum(yh)

    # Get mininmum level
    yh_i = 0.0 ; i=0
    if (low <= 0.0):
        lev_min = min_val
    else:
        while (yh_i < low*yhtot):
            yh_i += yh[i]
            i += 1
        lev_min = (max_val - min_val)*(float(xh[i-1])/255.0) + min_val

    # Get maximum level
    yh_i = 0.0 ; i=0
    if (high >= 1.0):
        lev_max = max_val
    else:
        while (yh_i < high*yhtot):
            yh_i += yh[i]
            i += 1
        lev_max = (max_val - min_val)*(float(xh[i-1])/255.0) + min_val   
    
    il = np.where(image <= lev_min)
    image[il] = lev_min
    ih = np.where(image >= lev_max)
    image[ih] = lev_max

    return image
    
    
