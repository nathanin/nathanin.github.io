import numpy as np
import tensorflow as tf
import time

from svs_reader import Slide

slide_path = '/home/ing/tmp_svs.svs'

# Set up a new slide that returns images in float32, via preprocess_fn
preprocess_fn = lambda x: (x / 255.).astype(np.float32)
svs = Slide(slide_path = slide_path,
            oversample_factor = 2.0,
            preprocess_fn = preprocess_fn)

# This function looks up coordinates then loads image content
def wrapped_fn(idx):
    coords = svs.tile_list[idx]
    img = svs._read_tile(coords)
    return img, idx

# mapped function produces image and index tuple. 
# the image is float, the index is int
def read_region_at_index(idx):
    return tf.py_func(func     = wrapped_fn,
                      inp      = [idx],
                      Tout     = [tf.float32, tf.int64],
                      stateful = False)

# The generator produces indices
ds = tf.data.Dataset.from_generator(generator=svs.generate_index,
    output_types=tf.int64)

# Then we use the py_func to translate the index into an (image, index)
ds = ds.map(read_region_at_index, num_parallel_calls=8)
ds = ds.batch(32)
ds = ds.prefetch(512)
iterator = ds.make_one_shot_iterator()
img_op, idx_op = iterator.get_next()

# Now start the queue and run images through
# Notice we're producing batches now! 
# Let's update our blue content function, and then use place_batch

def blue_content(imgs):
    return np.mean(imgs[:,:,:,1], axis=(1,2))

svs.initialize_output(name='blue', dim=1, mode='tile')
with tf.Session() as sess:
    tstart = time.time()
    while True:
        try:
            img_, idx_ = sess.run([img_op, idx_op])
            blue_result = blue_content(img_)
            svs.place_batch(xs=blue_result, idxs=idx_, name='blue', mode='tile')
        except tf.errors.OutOfRangeError:
            tend = time.time()
            print('Iterator exhausted')
            break

print('processed {} tiles'.format(len(svs.tile_list)))
print('tdelta = {:3.5f}'.format(tend-tstart))
