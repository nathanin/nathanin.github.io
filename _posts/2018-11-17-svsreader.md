---
title: "SVS-Reader: the one-stop interface for reading Aperio SVS in Python"
tags: [svs-reader]
---

View the SVS-reader [project](https://github.com/BioImageInformatics/svs_reader).

Probably the most popuplar (and sensible) ways to store huge images, sometimes greater than 50,000 px per edge, is as a TIFF pyramid. With a pyramid, we only save a few discrete magnification levels, letting viewing software interpolate between the levels, and only pull in only the image data needed for the current field of view. Aperio's SVS format (Lieca Biosystems, now owned by Philips (?)) uses this image pyramid to store images from their whole slide scanners. The formatting choice is appropriate, given that tissues have multi-scale information. That is, there are structures visible at low-magnification that we lose at high magnification, but also high power only features that are averaged over at lower resolutions. In this post, I am going to showcase a python class for working with these images by detailing the development of an application to tally the area of cancer in a set of TCGA slides.

For the purposes of this post, I have a directory filled with the TCGA PRAD (Prostate Adenocarcinoma) diagnostic images (`-01Z-`), downloaded from the genomic data commons data portal. We can see that at an average of 1GB, each file is quite a bit larger than your typical JPEG image. 

    $ du -sh /mnt/D/svs/TCGA_PRAD/
    226G	/mnt/D/svs/TCGA_PRAD/

    $ ls /mnt/D/svs/TCGA_PRAD/*svs | wc -l
    222

![QuPath screenshot]({{ site.baseurl }}/assets/svsreader_qupath_screenshot.png)

There exist several capable tools for viewing, and analysing images such as these. My favorite is [`QuPath`](https://qupath.github.io) (screenshot above). SVS reader isn't nearly as beautiful as QuPath. But, let's say we're not wanting or needing to manually annotate all these images ourselves. For that we need to do some scripting, and as of today, the leading open source interface that works on all types of bioformat images is [`OpenSlide`](https:openslide.org). Let's say our use case is this: we have a program that will tell us the size of tumor on each slide, and we want to run it on all the slides in some directory. I would build this program using `SVS-Reader`. SVS-Reader is essentially a wrapper for `openslide` that lets me work with svs files quickly and painlessly. It deals with reading, preprocessing, feeding tiles, and storing results. 

SVS-Reader is implemented as a python class that, once instantiated, will apply a set of prescribed opreations to the target file, and return a class ready for processing. These are the bullet points:
* We often think about tiny parts of the whole slide as *tiles*. The number of tiles yielded by a slide can be between 100 and 10,000 depending on many factors.
* Tissues are scanned as rectangles although they are almost never rectangular. We can discard that area and focus only on the foreground. We do this approximately, at the lowest magnification and optionally with higher magnification refinement. The idea is to exclude big chunks of image at once, without excluding anything we'll eventually want to analyze.
* SVS-reader is set up to support *data parallel* applications. While we can use it to read and process big chunks of image, or even whole magnification levels at a time, this case may be better handled using `openslide` directly.
* The main attribute of the `Slide` class is the tile-coordinate pairing that allows us to generate tiles in arbitrary order in support of data parallel applications. It's highly recommended to use a RAM disk or SSD.


## The Slide object

To set up the slide object with default settings, do the following. Make sure you have `openslide-python` installed first. Print info is pretty verbose, printing every internal attribute that the Slide object keeps track of. Somewhere in the middle we see `tile_list`. This list is a list of (index, x-y coordinate) tuples, and it is the key item that makes the Slide object useful. I also want to point out `ds_tile_map`. This unassuming matrix is the co-star. This is a downsampled numpy array, whose elements correspond to a particular tile in the real svs image. These elements store the index values we need to go between the random-access list and the spatially conserved svs-space.

```python
from svs_reader import Slide

svs_file = '/path/to/my/file.svs'
svs = Slide(slide_path = svs_file)

svs.print_info()
```

I'm struggling with whether or not to include this next section about the instantiation procedures. It might get dense. This is also the part where I talk about what all the settings are, and do. Since the people who read this will probably be equipped to open up slide.py and make some changes, I want to have it here for completeness. If you don't care, you can skip forward to the analysis example. 

The order of operations that we do in order to arrive at our `tile_list` and `ds_tile_map` arose from a workflow that I had in palce for working with just ordinary large images. First we call up a function to parse the information from the svs file, we need three things: the size of each level, how many levels there are, and what the high level magnification is.


## My first workflow

Remember that we're using the *tile* as our atomic unit. Each of our tiles is by default going to be 256 x 256 px, RGB-channel uint8 representing an image at 10X magnification. Pretend we have a function that takes such an input and returns a scalar output: the red intensity in the tile. We want to take this function and apply it to every tile in the svs file. More than that, we need to track the results. We initialize an output image with a unique name, the number of outputs per tile, and tell it that we're in "tile" mode, and that this output tracks scalars, or 1D vector outputs for each tile. Then, we simply iterate using the Slide's `generator`, storing the output each time. For now, I'm not including a built-in `apply()` method because the single-threaded case is trivial (the code below is all it is) and the parallel case we'll get to next.

I ran the example with default settings to see roughly how long it takes. I have a spinning HDD (7200 RPM), a SATA SSD, and a RAM drive to test. View the [code]({{ site.baseurl }}/assets/svsreader_generator.py).
```
SVS-reader built-in generator time to read all tiles:

oversample factor = 1.25
processed 9567 tiles
tdelta = 96.31615

oversample factor = 2.0
processed 24743 tiles
tdelta = 232.51319
```

## An actually usable workflow

Queues are great. SVS-reader is made to facilitate data parallelism. We make the core assumption that the process applied to an individual tile is independent of the surrounding tiles. A large assumption, I know. In the cases when this assumption holds, we can get many fold speed imporvements by asynchronously processing tiles, and using our best friend `ds_tile_map` to put the results in the proper place.

This part is a little messy. I like to use `TensorFlow` datasets to implement queuing. More often than not the processing is also a TensorFlow implemented CNN, so it makes sense to implement feeding the SVS data as part of the graph. Unfortunately, the code becomes a little convolved since the op to grab the next image is implemented via a `tf.py_func` op. First, we have to generate an *index*, then use the Slide object's internal functions to look up the coordinates associated with that index in `tile_list`, and return the proper image data.

Notice that we're producing batches, but the contents of these batches can be from various parts of the slide.

View the [code]({{ site.baseurl }}/assets/svsreader_tfdataset.py). As expected the time increases linearly with the number of tiles, and we see a 3X speed up!
```
SVS-reader with TensorFlow dataset for multithreading:

oversample_factor = 1.25
processed 9567 tiles
tdelta = 32.59452

oversample_factor = 2.0
processed 24743 tiles
tdelta = 84.63335
```