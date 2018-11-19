import numpy as np
import time

from svs_reader import Slide
slide_path = '/home/ing/tmp_svs.svs'

svs = Slide(slide_path = slide_path,
            oversample_factor = 2.0)

def blue_content(tile):
    blue_channel = tile[:,:,1]
    return np.mean(blue_channel)

svs.initialize_output(name='blue', dim=1, mode='tile')
print(svs.output_imgs['blue'].shape)

tstart = time.time()
for img, idx in svs.generator():
    blue_result = blue_content(img)
    
    # place the result into the output image we just initialized
    svs.place(x=blue_result, idx=idx, name='blue', mode='tile')

tend = time.time()

print('processed {} tiles'.format(len(svs.tile_list)))
print('tdelta = {:3.5f}'.format(tend-tstart))
