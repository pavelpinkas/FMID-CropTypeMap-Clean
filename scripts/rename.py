#!/usr/bin/env python3

import os
import shutil
import re

SHP_EXTENSIONS      = ['.shp', '.shx', '.dbf', '.prj']
IMG_EXTENSIONS      = ['.tif']

IMG_RGX             = "([a-zA-Z]{2})(.*)"

files = os.listdir ()

for f in files:
    base, ext = os.path.splitext (f)
    if ext in SHP_EXTENSIONS:
        base = base.upper ()
        newName = base + ext 
        
    elif ext in IMG_EXTENSIONS:
        match = re.match (IMG_RGX, f)
        if match is not None:
            state = match.group (1).upper ()
            rest = match.group (2)
            newName = state + rest 
            
    if newName != f:
        shutil.move (f, newName)
        
