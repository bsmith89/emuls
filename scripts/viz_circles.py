#!/usr/bin/python3
"""Create image files with circle perimeters added.

"""
import sys
from find_circles import renorm, threshold, read_circles
from skimage.io import imread, imsave
from matplotlib import pyplot as plt
from skimage import color
from skimage.draw import circle
from numpy import zeros

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

def main():
    in_image = sys.argv[1]
    out_image = sys.argv[2]
    image = renorm(imread(sys.argv[1]))
    circles = read_circles(sys.stdin)
    overlaid = add_circles(image, circles)
    imsave(sys.argv[2], overlaid)

if __name__ == '__main__':
    main()
