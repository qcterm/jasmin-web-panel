"MESH50 Route System"

import random
user = routable.user.uid

# get config for user
cfg = {'silent': 0.5}
silent = 0
if cfg is not None:
    if 'silent' in cfg:
        silent = cfg['silent']

v = random.random()
if v <= silent:
    result = True
else:
    result = False
