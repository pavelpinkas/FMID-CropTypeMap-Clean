#!/usr/bin/env python 3

import sys 
import os 
import re 
import shutil 

import numpy 

from osgeo import gdal 
from osgeo import gdalconst as GC 

class CLUResultMerge:
    ''' Merges the cleaned up result from CLUCalculator with the 
        raw maps. Areas covered by CLU data (and thus cleaned 
        from pixel scatter by the CLUCalculator) are taken from clean 
        version of the maps, while the areas not covered by 
        CLU data come from the raw maps '''
    
    DEFAULT_BAND            = 1
    
    SHP_EXTENSION           = ".shp"
    TIF_EXTENSION           = ".tif"
    
    RGX_MAP_FILE            = "[a-zA-z]{2}\\.tif$"
    
    BASEMAP_FMT             = "{0}19_17crops-s8.tif"
    
    def __init__ (self, cleanMapsPath, baseMapsPath, cluPath, outPath):
        ''' constructor 
        
            @param cleanMapsPath: path to clean maps 
            @param baseMaps: path to raw maps 
            @param cluPath: path to CLU masks 
            @param outPath: where the results are writen '''
        
        self.CleanMapsPath = cleanMapsPath
        self.BaseMapsPath = baseMapsPath
        self.CLUPath = cluPath
        self.OutputPath = outPath 
        
    def merge (self):
        ''' perform the merge ''' 
        
        if not os.path.exists (self.OutputPath):
            os.mkdir (self.OutputPath)
            
        files = sorted (os.listdir (self.CleanMapsPath))
        for f in files:
            if re.match (self.RGX_MAP_FILE, f):
                sys.stdout.write ("Merging {0} ...\n".format (f))
                sys.stdout.flush ()
                self.merge1 (f)
                
    def merge1 (self, filename):
        ''' perform merge on one file 
         
            @param filename: name of the file '''
        
        base, _ext = os.path.splitext (filename)
        
        cluBase, cluExt = os.path.splitext (filename)
        cluFilename = cluBase + "-clu" + cluExt
        cluFile = os.path.join (self.CLUPath, cluFilename)

        cleanMapFile = os.path.join (self.CleanMapsPath, filename)
        baseMapFile = os.path.join (self.BaseMapsPath, filename)
    
        # get the raster of clean map 
        cleanDataset = gdal.Open (cleanMapFile, GC.GA_ReadOnly)
        cleanLayer = cleanDataset.GetRasterBand (self.DEFAULT_BAND)
        cleanData = cleanLayer.ReadAsArray ().astype (numpy.byte)
        cleanDataset = None 

        # create CLU mask (1 where CLU data are known, 0 elsewhere)
        if os.path.exists (cluFile):
            cluDataset = gdal.Open (cluFile, GC.GA_ReadOnly)
            cluLayer = cluDataset.GetRasterBand (self.DEFAULT_BAND) 
            cluMask = cluLayer.ReadAsArray ()
            cluMask = (cluMask != 0)
            cluMask = cluMask.astype (numpy.byte)
            cluDataset = None
        else:
            cluMask = numpy.ndarray (shape = cleanData.shape)
            cluMask.fill (0)    # if CLU dataset does not exist, the mask is empty 
                                # but still needs to be created 
        
        # same for the data from raw (base) map
        baseDataset = gdal.Open (baseMapFile, GC.GA_ReadOnly)
        baseLayer = baseDataset.GetRasterBand (self.DEFAULT_BAND)
        baseData = baseLayer.ReadAsArray ().astype (numpy.byte)
        baseDataset = None
        
        # combine clean and raw layer - use clean data where 
        # CLU mask is 1 and raw data everywhere else 
        mergedData = cluMask * cleanData + (1 - cluMask) * baseData 
        
        # create output file 
        outputName = os.path.join (self.OutputPath, filename)
        shutil.copy (baseMapFile, outputName)
        outputDataset = gdal.Open (outputName, GC.GA_Update)
        outputLayer = outputDataset.GetRasterBand (self.DEFAULT_BAND)
        outputLayer.WriteArray (mergedData)
        outputDataset = None 
        
        
if __name__ == "__main__":
    REQUIRED_ARGUMENTS = 4
    
    nArgs = len (sys.argv[1:])
    
    if nArgs != REQUIRED_ARGUMENTS:
        sys.stderr.write ("\nUSAGE: [python] CLUResultMerge.py clean-path base-path clu-path out-path\n\n")
        
    else:
        clean, base, clu, out = sys.argv[1:]
        
        clurm = CLUResultMerge (clean, base, clu, out)
        clurm.merge ()
        
        