from osgeo import gdalconst as GConst 
from osgeo import gdal 

import numpy as NPy 

from scipy import ndimage 
from scipy.ndimage import morphology 

import shutil 
import sys 
import os 

class DeNoiseFilter:
    ''' denoising filter with focus on preserving data consistency (over 
        the visual appeal of the denoised data) '''

    DEFAULT_REMOVE_THRESHOLD            = 7
    DEFAULT_FILL_THRESHOLD              = 30
    DEFAULT_FILL_FLAG                   = False 
    DEFAULT_REMOVE_FLAG                 = True

    def __init__ (self, *, removeThreshold: int = DEFAULT_REMOVE_THRESHOLD,
                           fillThreshold: int = DEFAULT_FILL_THRESHOLD,
                           fillFlag = DEFAULT_FILL_FLAG,
                           removeFlag = DEFAULT_REMOVE_FLAG):
        ''' initializer 

            @param removeThreshold: all pixel clusters equal or smaller will be removed
            @param fillThreshold: only holes small or equal will be filled 
            @param fillFlag: if True, hole filling will be performed, otherwise not 
            @param removeFlag: if True, small pixel removal will be performed '''

        self.DeClutterFlag = removeFlag
        self.CoreFillFlag = fillFlag
        self.DeClutterThreshold = removeThreshold
        self.CoreFillThreshold = fillThreshold

    def findSurvivors (self, segments, nFeatures):
        ''' catalog value distribution inside the image 
        
            @param segments: labeled image 
            @param nFeatures: number of continuous segments in image
            @return: IDs of all segments that satisfy the threshold''' 

        h = NPy.histogram (segments, range (1, nFeatures + 1))
        survivors = h[1][NPy.where (h[0] >= self.DeClutterThreshold)]

        return survivors

    def apply (self, inputf: str, outputf: str):
        ''' apply the filter 

            @param inputf: input data 
            @param outputf: processing results '''

        dsInput = gdal.Open (inputf, GConst.GA_ReadOnly)
        b1 = dsInput.GetRasterBand (1)
        img = b1.ReadAsArray ()
        dsInput = None 

        img = self.declutter (img)
        img = self.corefill (img)

        shutil.copy (inputf, outputf) # fast way to clone the entire dataset 

        dsOutput = gdal.Open (outputf, GConst.GA_Update)
        b1 = dsOutput.GetRasterBand (1)
        b1.WriteArray (img)
        dsOutput = None

    def corefill (self, img: NPy.ndarray) -> NPy.ndarray:
        ''' apply hole filling '''

        if self.CoreFillFlag:
            raise Exception ("The core filling functionality not implemented yet") 

        return img

    def declutter (self, img: NPy.ndarray) -> NPy.ndarray:
        ''' apply removal of small pixels
        
            @param img: img to remove small clusters from  '''

        CONNECT_8WAY = NPy.ones (shape = (3, 3), dtype = NPy.int)

        if self.DeClutterFlag:
            segments, nSegments = ndimage.label (img, structure = CONNECT_8WAY)
            survivors = self.findSurvivors (segments, nSegments)
            mask = NPy.isin (segments, survivors).astype (NPy.uint8)
            img = img * mask 

        return img 

# ..................................... MAIN ................................

if __name__ == "__main__": 
    
    REQUIRED_ARGS = len ([(INPUT_INDEX  := 0), 
                          (OUTPUT_INDEX := 1)]) 

    args = sys.argv[1:]
    nArgs = len (args)

    if nArgs == REQUIRED_ARGS:
        inputf, outputf = args 
        dnf = DeNoiseFilter ()
        dnf.apply (inputf, outputf)

    else:
        app = os.path.basename (sys.argv[0])
        sys.stderr.write (f"\nuSAGE: {app} input.tif output.tif\n\n")