from RasterUtils import RasterUtils
from DeNoiseFilter import DeNoiseFilter
from MultiColorSweep import MultiColorSweep
from ProductFinalizer import ProductFinalizer 

import numpy as NPy

from Utils.TmpFileUtils import TmpFileUtils
from Extractors.PLD.MajorityFilter import MajorityFilter

from typing import Union, Optional

class RegionCleanup:
    ''' top driver for single region cleanup '''

    FILTER_TYPES            = [(MCQ_FILTER      := "mcq"),
                               (DENOISE_FILTER  := "denoise"), 
                               (MAJORITY_FILTER := "majority")]

    MCQ_THRESHOLD           = 7
    MAJORITY_KERNEL_SIZE    = 5

    def __init__ (self):
        ''' initializer '''

    def run (self, inputf: str, 
                   outputf: str, 
                   productf: str, 
                   proj4: str,
                   xres: float, 
                   yres: float,
                   nvreplace: Optional[Union[float, int]] = None,
                   filterChoice: str = DENOISE_FILTER):

        ''' run the cleanup procedure 

            @param inputf: input data 
            @param outputf: product of cleanup procedure
            @param product: final product with reprojection and resizing 
            @param proj4: projection for final product 
            @param xres: X-resolution of the final product 
            @param yres: Y-resolution of the final pproduct 
            @param nvreplace: replacement value for no-data pixels 
            @param filterChoice: which filter to use '''

        self.applyFilter (inputf, outputf, filterChoice)
        self.finalizeProduct (outputf, productf, proj4, xres, yres)
        self.nvReplace (productf, nvreplace) 

    def applyFilter (self, inputf: str, outputf: str, filterChoice: str):
        ''' apply denoising filter to the raw pixel map 

            @param inputf: input file (raw map)
            @param outputf: output file (denoised map) 
            @param filterChoice: which filter to use '''

        if filterChoice == self.DENOISE_FILTER:
            dnf = DeNoiseFilter (fillFlag = False, removeFlag = True)
            dnf.apply (inputf, outputf)

        elif filterChoice == self.MCQ_FILTER:
            mcq = MultiColorSweep (inpFile = inputf,
                                   outFile = outputf,
                                   minSize = self.MCQ_THRESHOLD,
                                   ignorenv = True)
            mcq.sweep ()

        elif filterChoice == self.MAJORITY_FILTER:
            neighborhood = NPy.ones (shape = (self.MAJORITY_KERNEL_SIZE, 
                                              self.MAJORITY_KERNEL_SIZE))
            mjf = MajorityFilter (neighborhood)
            mjf.filter (inputf, outputf)

    def finalizeProduct (self, basemap: str,
                               product: str, 
                               projection: str,
                               xresolution: float,
                               yresolution: float):

        ''' reproject to desired projection and adjust resolution 
            
            @param basemap: dataset to finalize 
            @param product: final product 
            @param projection: product projection 
            @param xresolution: X-resolution of the product 
            @param yresolution: Y-resolution of the product '''

        pf = ProductFinalizer (source = basemap,
                               product = product,
                               xres = xresolution,
                               yres = yresolution,
                               proj4 = projection)

        pf.process ()

    def nvReplace (self, datafile: str, replacement: Union[float, int, None]):
        ''' replace the no-value pixels with pixels of set value 

            @param datafile: file to operate on 
            @param replacement: replacement value for no data pixels '''

        RasterUtils.undeclareNoDataValue (datafile, replacement)

# ................................... MAIN ..................................

import sys 
import os 

if __name__ == "__main__":
    
    REQUIRED_ARGS = 3 
    
    args = sys.argv[1:]
    nArgs = len (args)

    if nArgs == REQUIRED_ARGS:
        inputf, outputf, productf = args
        rc = RegionCleanup ()
        rc.run (inputf = inputf, 
                outputf = outputf, 
                productf = productf, 
                proj4 = "+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs",
                xres = 30,
                yres = 30, 
                nvreplace = 0) 

    else:
        app = os.path.basename (sys.argv[0])
        sys.stderr.write (f"\nUSAGE: {app} input.tif denoised.tif product.tif\n\n")
        