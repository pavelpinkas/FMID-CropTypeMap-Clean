#!/usr/bin/env python3 

from osgeo import gdal 
from osgeo import gdalconst as GC 

import numpy as NP

import os 

class ColorSplitter:
    ''' takes a multicolor GTiff files and generates a collection of 
        single layer GTiff files, each only containting pixels of 
        one color - the rest of pixels are set to NO_VALUE '''

    DEFAULT_NO_DATA_VALUE           = 0
    DEFAULT_BAND                    = 1
    DEFAULT_BLOCK_SIZE              = 10000
    
    OUTNAME_FMT                     = "{base}-{number:2}{ext}"
    
    def __init__ (self, 
                  image, 
                  noDataValue = DEFAULT_NO_DATA_VALUE,
                  blockSize = DEFAULT_BLOCK_SIZE):
        
        ''' constructor 
        
            @param image: image to split
            @param noDataValue: custom value to represent no data,
            @param blockSize: blocks size (in lines) for reading huge images  '''
        
        self.Image = image 
        self.NoDataValue = noDataValue
        self.BlockSize = blockSize 
        
    def split (self):
        ''' perform the split '''
        
        dataset = gdal.Open (self.Image, GC.GA_ReadOnly)
        colors = self.listColors (dataset)
        print (colors)
        
        basename, extension = os.path.splitext ()
        iColor = 0 
        driver = gdal.GetDriverByName ('GTiff')
        
        for c in colors:
            iColor += 1 
            outputName = self.OUTNAME_FMT.format (base = basename,
                                                  number = iColor,
                                                  ext = extension)
#             outds = driver.Create (outputName, )
#             pixelMask = data[data == c]
            
        
        dataset = None # done with image 
        
    def listColors (self, dataset):
        ''' find unique values in an array, no counting the 
            NO_DATA_VALUE pixels 
            
            @param dataset: open dataset containing the image ot operate on
            @param return: list of unique items found ''' 
        
        band = dataset.GetRasterBand (self.DEFAULT_BAND)
        
        uniques = [] 
        done = False 
        iBlock = 0
        blockSize = self.BlockSize 
        
        while not done: 
            startRow = iBlock * blockSize 
            endRow = startRow + blockSize - 1 
            
            if endRow >= band.YSize:
                blockSize = band.YSize - startRow 
                done = True
        
            data = band.ReadAsArray (0, startRow, band.XSize, blockSize)
            data = data[data != self.NoDataValue]
            unique = NP.unique (data)
            uniques.extend (unique)
            
            iBlock += 1
            
        uniques = list (set (uniques))
            
        return uniques
    
# ...........................................................................

if __name__ == "__main__":
    cs = ColorSplitter ("../data/Merged/CONUS_CT_2019.tif")
    cs.split ()
    