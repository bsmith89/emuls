#!/usr/bin/env python3
"""Estimate the location and size of circles in a darkfield image.

Useful for measuring microdroplet size distributions.

Pipeline:
    1.  Normalize image in uint8 space (min=0, max=iinfo(uint8).max)
    2.  Locally threshold image
    3.  Hough transform threshold image over a evenly spaced series of radii
    4.  Gaussian blur this Hough volume
    5.  Find local maxima within blurred volume
    6.  Retrieve Hough accum value ("score") for each local peak
    7.  Filter out local maxima with accum values below a threshold
    8.  Return coordinates of estimated circles
"""

import sys
from numpy import array, column_stack, iinfo, uint8, asarray, empty
from skimage import filter as image_filter
from skimage.transform import hough_circle
from skimage.feature import peak_local_max
from skimage.color import gray2rgb
from skimage.io import imread, imsave
from scipy.ndimage.filters import gaussian_filter
from matplotlib import pyplot as plt
from matplotlib import cm
from numpy import zeros, arange
from skimage.draw import circle
from scipy.interpolate import interp1d
from pandas import DataFrame, read_table


def renorm(image, dtype=uint8):
    output = image - min(image.flat)
    output = output * (float(iinfo(dtype).max) / max(output.flat))
    return output.astype(dtype)

def threshold(image, block_size=100, offset=-5):
    return image_filter.threshold_adaptive(renorm(image),
                                           block_size=block_size,
                                           offset=offset)

def find_circles(image, min_r=30, max_r=300, cutoff=0.5, step=4, blur_sigma=3):
    rs = arange(min_r, max_r, step)
    threshold_image = threshold(image)
    hough_space = hough_circle(threshold(image), rs)
    sigma_3d = (blur_sigma,
                blur_sigma,
                float(blur_sigma) / step)
    blurred_hough_space = gaussian_filter(hough_space, sigma=sigma_3d)
    local_maxima = peak_local_max(blurred_hough_space, exclude_border=False)
    circles = column_stack((local_maxima, hough_space[tuple(local_maxima.T)]))
    circles[:,0] = rs[list(circles[:,0])]
    return circles[circles[:,3] > cutoff]

def circles2df(circles):
    df = DataFrame(circles, columns=("r", "x", "y", "score"))
    df[['r', 'x', 'y']] = df[['r', 'x', 'y']].astype(int)
    return df

def save_circles(circles, handle=sys.stdout):
    df = circles2df(circles)
    df.to_csv(handle, sep="\t", na_rep="NaN", index=False)

def read_circles(handle=sys.stdin):
    df = read_table(handle)
    return df[['r', 'x', 'y', 'score']].values

def main():
    image = renorm(imread(sys.argv[1]))
    circles = find_circles(image)
    save_circles(circles, sys.stdout)


if __name__ == '__main__':
    main()
