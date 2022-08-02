from RasterUtils import RasterUtils

from osgeo import gdalconst as GConst  
from osgeo import gdal 

import numpy as NPy 
import shutil

from typing import Union 

class PreferredValue:
    ''' allows forcing pixels of certain value as always included '''

    def __init__ (self, preferredValue: Union[float, int]):
        ''' initializer 

            @param preferredValue: pixel value to prefer ''' 

        self.PreferredValue = preferredValue

    def process (self, inputf: str, outputf: str, preferredf: str):
        ''' perform pixel forcing 
        
            @param inputf: original dataset 
            @param outputf: resulting dataset 
            @param preferredf: dataset with location of preferred value pixels '''

        dsIn = gdal.Open (inputf, GConst.GA_ReadOnly)
        inBand = dsIn.GetRasterBand (1)
        inData = inBand.ReadAsArray () 
        dsIn = None

        prefIn = gdal.Open (preferredf, GConst.GA_ReadOnly)
        prefBand = prefIn.GetRasterBand (1)
        prefData = prefBand.ReadAsArray ()
        prefIn = None

        mask = (prefData == self.PreferredValue)
        inData[mask] = self.PreferredValue

        shutil.copy (inputf, outputf)
        dsOut = gdal.Open (outputf, GConst.GA_Update)
        outBand = dsOut.GetRasterBand (1)
        outBand.WriteArray (inData)
        dsOut = None  

# ----------------------------------- MAIN ----------------------------------

import sys 
import os 

from ProductFinalizer import ProductFinalizer

if __name__ == "__main__":

    REQUIRED_ARGS = 2
    args = sys.argv[1:]
    nArgs = len (args)

    if nArgs == REQUIRED_ARGS:
        dataPath, basemapPath = args 

        DATA_SUBPATH        = "merged"
        RESULT_SUBPATH      = "merged2"
        PRODUCT_SUBPATH     = "product"

        BASEMAP_FMT         = "{0}2020_20200711.tif"
        REGION_FMT          = "{0}.tif"

        XRES_PRODUCT        = 30
        YRES_PRODUCT        = 30

        NO_DATA_VALUE_REPLACEMENT = 0
        FINAL_PROJECTION = "+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs"

        subdirs = sorted (os.listdir (dataPath))

        for sd in subdirs:
            sys.stdout.write (" -> Postprocessing {0} ... \n".format (sd.upper ())) 
            sys.stdout.flush ()

            basemap = BASEMAP_FMT.format (sd.upper ())
            regionf = REGION_FMT.format (sd.lower ())
            basemap = os.path.join (basemapPath, basemap)
            inputf = os.path.join (dataPath, sd.upper (), DATA_SUBPATH, regionf)
            outputf = os.path.join (dataPath, sd.upper (), RESULT_SUBPATH, regionf)
            productf = os.path.join (dataPath, sd.upper (), PRODUCT_SUBPATH, regionf)

            pv = PreferredValue ((PRIORITY_COLOR := 0))
            pv.process (inputf, outputf, basemap)

            pf = ProductFinalizer (source = outputf,
                                   product = productf, 
                                   xres = XRES_PRODUCT,
                                   yres = YRES_PRODUCT,
                                   proj4 = FINAL_PROJECTION)
            pf.process ()

            RasterUtils.undeclareNoDataValue (productf, NO_DATA_VALUE_REPLACEMENT)

    else:
        app = os.path.basename (sys.argv[0])
        sys.stderr.write (f"\nUSAGE: {app} datasets basemaps \n\n")