#!/usr/bin/env python3
"""Estimate the location and size of circles in a darkfield image.

Useful for measuring microdroplet size distributions.

Pipeline:
    1.  Normalize image in uint8 space (min=0, max=iinfo(uint8).max)
    2.  Locally threshold image
    3.  Hough transform threshold image over a geometrically increasing
        series of radii
    4.  Interpolate intervening Hough volume
    5.  Gaussian blur full Hough volume
    6.  Find local maxima within blurred volume
    7.  Retrieve interpolated Hough accum value ("score") for each local peak
    8.  Filter out local maxima with accum values below a threshold
    9.  Return coordinates of estimated circles
"""

import sys
from numpy import array, column_stack, iinfo, uint8, asarray, empty
from skimage import filter as image_filter
from skimage.transform import hough_circle
from skimage.feature import peak_local_max
from skimage.color import gray2rgb
from skimage.draw import circle_perimeter
from skimage.io import imread, imsave
from scipy.ndimage import filters as ndfilters
from matplotlib import pyplot as plt
from matplotlib import cm
from numpy import zeros
from skimage import color
from skimage.draw import circle
from scipy.interpolate import interp1d
from pandas import DataFrame


def renorm(image, dtype=uint8):
    output = image - min(image.flat)
    output = output * (float(iinfo(dtype).max) / max(output.flat))
    return output.astype(dtype)

def image_grid(*images, fig_height=5, max_cols=3, kwargs_list=None, **kwargs):
    """Print a grid of identically shaped images.

    Identical shape is assumed, not checked.

    Returns fig, [axes]

    """
    plots_high = int(len(images) / max_cols) + 1
    plots_wide = min(max_cols, len(images))
    dim_ratio = (images[0].shape[0] * plots_high) / (images[0].shape[1] * plots_wide)
    fig = plt.figure(figsize=(fig_height / dim_ratio, fig_height))
    axes = []
    if not kwargs_list:
        kwargs_list = asarray([kwargs] * len(images))
    else:
        assert len(kwargs_list) == len(images)
    for i, img in enumerate(images):
        axis = fig.add_subplot(plots_high, plots_wide, i + 1)
        axis.imshow(img, **kwargs_list[i])
        axes.append(axis)
    return fig, axes


def threshold(image, block_size=100, offset=-5):
    return image_filter.threshold_adaptive(renorm(image),
                                           block_size=block_size,
                                           offset=offset)

def increasing_distance(a, b=None, factor=1.05, inclusive=True):
    """Create a list of integers with increasing distance between them.

    This is useful for sampling more sparsely at higher values.
    """
    def _increasing_distance():
        assert factor > 1
        if b:
            start = a
            stop = b
        else:
            start = 1
            stop = a
        assert start == int(start)
        assert stop == int(stop)

        val = start
        while True:
            if val < stop:
                yield val
            if val >= stop:
                if inclusive:
                    yield val
                return
            val = max(val + 1, int(val * factor))
    return array(list(_increasing_distance()))

def hough_transform_interp(a, rs):
    calculated = hough_circle(a, rs)
    interp = interp1d(rs, calculated, axis=0)
    return interp(range(min(rs), max(rs)))

def add_circles(image, circles, cmap=plt.cm.cool):
    output = color.gray2rgb(image)
    for r, x, y, accum in circles:
        shape = list(reversed(image.shape))
        xs_outer, ys_outer = circle(y, x, r, shape=shape)
        xs_inner, ys_inner = circle(y, x, r - 3, shape=shape)
        c_img = zeros(image.shape, dtype=bool)
        c_img[ys_outer, xs_outer] = 1
        c_img[ys_inner, xs_inner] = 0
        color_value = cmap(accum, bytes=True)[:-1]
        output[c_img] = color_value
    return output

def find_circles(image, cutoff=0.5):
    rs = increasing_distance(30, 300, 1.05)
    threshold_image = threshold(image)
    hough_space = hough_transform_interp(threshold(image), rs)
    blurred_hough_space = ndfilters.gaussian_filter(hough_space, sigma=(3, 3, 3))
    local_maxima = peak_local_max(blurred_hough_space, exclude_border=False)
    outlines = column_stack((local_maxima, hough_space[tuple(local_maxima.T)]))
    outlines[:,0] = outlines[:,0] + min(rs)
    return outlines[outlines[:,3] > cutoff]

def main():
    image = renorm(imread(sys.argv[1]))
    circles = find_circles(image)
    df = DataFrame(circles, columns=("r", "y", "x", "score"))
    df[['r', 'y', 'x']] = df[['r', 'y', 'x']].astype(int)
    df.to_csv(sys.stdout, sep="\t", na_rep="NaN", index=False)


if __name__ == '__main__':
    main()
