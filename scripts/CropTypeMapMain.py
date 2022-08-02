#!/usr/bin/env python3 

# ------------------------------- LAUNCH SCRIPT -----------------------------

import sys
import re 
import os 
import shutil

from Utils.TmpFileUtils import TmpFileUtils 
from RegionCleanup import RegionCleanup

from typing import List

if __name__ == "__main__":
    
    REQUIRED_ARGS = 2 

    PRODUCT_PROJ4 = "+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs"
    PRODUCT_XRES  = 30
    PRODUCT_YRES  = 30

    args = sys.argv[1:]
    nArgs = len (args)

    if nArgs == REQUIRED_ARGS:
        RGX_MAP_NAME = "([a-z,A-Z]{2}).tif$"

        # REGIONS = ["AL", "AR", "CO", "FL", 
        #            "GA", "IA", "ID", "IL",
        #            "IN", "KS", "KY", "LA",
        #            "MD", "MI", "MN", "MO",
        #            "MS", "MT", "NC", "ND",
        #            "NE", "NJ", "NY", "OH",
        #            "OK", "PA", "SC", "SD",
        #            "TN", "TX", "VA", "WA",
        #            "WI", "WV"]

        # REGIONS = ["ID", "KS", "MT", "ND", 
        #            "NE", "OH", "OK", "SD",
        #            "TN", "WA"]

        # SKIP    = ["MT", "TX"]
        # SKIP    = ["ID", "MT", "ND", "NE", "OH", 
        #            "OK", "SD", "TN", "WA"]

        REGIONS = ["AL", "AR", "CO", "FL", "GA",
                   "IA", "ID", "IL", "IN", "KS",
                   "KY", "LA", "MD", "MI", "MN",
                   "MO", "MS", "MT", "NC", "ND",
                   "NE", "NJ", "NY", "OH", "OK",
                   "PA", "SC", "SD", "TN", "TX",
                   "VA", "WA", "WI", "WV"]

        SKIP: List[str] = []
        
        # SKIP: List[str] = []

        mapdir, productdir = args
        basemaps = sorted (os.listdir (mapdir))

        if os.path.exists (productdir):
            shutil.rmtree (productdir)

        if not os.path.exists (productdir):
            os.makedirs (productdir)

        AUXILIARY_DIRECTORIES = [(RAW_SUBDIR     := "raw"), 
                                 (CLEANED_SUBDIR := "clean"), 
                                 (PRODUCT_SUBDIR := "product")]

        TmpFileUtils.init (prefix = "ctm2020", suffix = ".ag")

        for basemap in basemaps:
            match = re.match (RGX_MAP_NAME, basemap)
            if match is not None:
                region = match.group (1).lower ()
                regionf = f"{region}.tif"
                regiondir = region.upper ()

                # if regiondir != "OH":
                #     continue

                if REGIONS is None or (regiondir in REGIONS and regiondir not in SKIP):
                    sys.stdout.write (f" -> Processing {regiondir} ...\n")
                    rawdir = os.path.join (productdir, regiondir, RAW_SUBDIR)
                    cleandir = os.path.join (productdir, regiondir, CLEANED_SUBDIR)
                    finaldir = os.path.join (productdir, regiondir, PRODUCT_SUBDIR)

                    for d in [rawdir, cleandir, finaldir]:
                        os.makedirs (d)

                    source = os.path.join (mapdir, basemap)
                    workmap = os.path.join (rawdir, regionf)
                    shutil.copy (source, workmap)

                    cleanMap = os.path.join (cleandir, regionf)
                    productMap = os.path.join (finaldir, regionf)

                    rc = RegionCleanup ()
                    rc.run (inputf = workmap, 
                            outputf = cleanMap, 
                            productf = productMap, 
                            proj4 = PRODUCT_PROJ4,
                            xres = 30,
                            yres = 30, 
                            nvreplace = 0,
                            filterChoice = RegionCleanup.MAJORITY_FILTER) 
                            # filterChoice = RegionCleanup.MCQ_FILTER) 

        TmpFileUtils.cleanup ()

    else:
        app = os.path.basename (sys.argv[0])
        sys.stderr.write (f"\nUSAGE: {app} mapdir productdir \n\n")
        