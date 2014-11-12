#!/usr/bin/env python3

import sys
from numpy import array, column_stack, iinfo, uint8
from skimage import filter
from skimage.transform import hough_circle
from skimage.feature import peak_local_max
from skimage.color import gray2rgb
from skimage.draw import circle_perimeter
from skimage.io import imread, imsave
from matplotlib import cm
from scipy.ndimage import filters as ndfilters


_DEFAULT_MAX_RADIUS = 150
_DEFAULT_MIN_RADIUS = 5
_DEFAULT_FACTOR = 1.05
_DEFAULT_BLUR_SIGMA = 1
_DEFAULT_RADIUS_BUFFER = 5
_DEFAULT_OFFSET = -5
_DEFAULT_ACCUM_CUTOFF = 0.75


def increasing_distance(a, b=None, factor=_DEFAULT_FACTOR, inclusive=False):
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

def renorm(image, dtype=uint8):
        output = image - min(image.flat)
        output = output * (float(iinfo(dtype).max) / max(output.flat))
        return output.astype(dtype)

def find_circles(edge_image, max_r):
    # These may be set as keyword arguments in the future:
    min_r = _DEFAULT_MIN_RADIUS
    buff = _DEFAULT_RADIUS_BUFFER
    sigma = _DEFAULT_BLUR_SIGMA
    factor = _DEFAULT_FACTOR

    low_r = max(1, int(min_r - buff))
    high_r = int(max_r * (factor ** buff))
    hough_radii = array(list(increasing_distance(low_r, high_r,
                                                 factor=factor,
                                                 inclusive=True)))
    # TODO: Use full_output=True in hough_circle.  Trim the output.
    # Consider the statistical properties of this kind of sampling.
    hough_stack = hough_circle(edge_image, hough_radii)
    hough_stack_blurred = ndfilters.gaussian_filter(hough_stack,
                                                    sigma=(sigma, sigma, 1))
    local_maxima = peak_local_max(hough_stack_blurred, exclude_border=False,
                                  min_distance=min_r)  # Not (2 * min_r)?

    # For each local peak, retrieve the accumulation matrix value as a
    # quality control parameter.
    accum_array = hough_stack[local_maxima[..., 0],
                              local_maxima[..., 1],
                              local_maxima[..., 2]]
    local_maxima = column_stack((local_maxima, accum_array))
    # Inefficient implementation:
    local_maxima[..., 0] = [hough_radii[r] for r in local_maxima[..., 0]]
    return local_maxima[(local_maxima[..., 0] >= min_r) *
                        (local_maxima[..., 0] <= max_r) *
                        (local_maxima[..., 3] > _DEFAULT_ACCUM_CUTOFF)]

def add_circles(image, circles, cmap=cm.cool):
    output = gray2rgb(image)
    height, width = image.shape  # Or should this be reversed?
    for r, x, y, accum in circles:
        xs, ys = circle_perimeter(int(y), int(x), int(r))
        coords = column_stack((xs, ys))
        coords = coords[(xs < width) * (ys < height), :]
        color_value = cmap(accum, bytes=True)[:-1]
        output[coords[:, 1], coords[:, 0]] = color_value
    return output

def main():
    image_paths = sys.argv[1:]
    for path in image_paths:
        image = renorm(imread(path))
        edges_image = filter.threshold_adaptive(image, _DEFAULT_MAX_RADIUS,
                                                offset=_DEFAULT_OFFSET)
        circles = find_circles(edges_image,
                               max_r=_DEFAULT_MAX_RADIUS)
        for c in circles:
            sys.stdout.write("\t".join(c.astype('str')))
            sys.stdout.write("\n")
        imsave("%s_circles.png" % path, add_circles(image, circles))
        imsave("%s_edges.png" % path, renorm(edges_image))

if __name__ == "__main__":
    main()
