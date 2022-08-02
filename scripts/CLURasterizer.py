#!/usr/bin/env python3 

from GeoTransform import GeoTransform
from CLUIdentifier import CLUIdentifier  # pylint: disable=unused-import
from CLUCalculator import CLUCalculator 

from osgeo import ogr 
from osgeo import gdalconst as GC 
from osgeo import gdal 

import os
import sys 

class CLURasterizer:
    ''' performs colored rasterization of shapefiles '''
    
    CMD_FMT      = "gdal_rasterize -co COMPRESS=LZW -co TILED=YES -te {xmin} {ymin} {xmax} {ymax} -tr {xstep} {ystep} -l {layer} -a {attr} {inp} {out}"
    OUTPUT_EXT   = ".tif"
    
    DEFAULT_BAND = 1
    
    def __init__ (self, filelist, colorAttr, basePath, verbose = False):
        ''' constructor 
        
            @param filelist: list of files to rasterize 
            @param colorAttr: attribute to color by 
            @param basePath: path to images to base rasterization on '''
        
        self.FileList = filelist 
        self.Verbose = verbose 
        self.ColorAttribute = colorAttr 
        
        self.BasePath = basePath
                
    def getLayerName (self, filename):
        ''' get a layer name from shapefile 
        
            @param filename: shapefile name 
            @return: layer name '''
        
        dataset = ogr.Open (filename, GC.GA_ReadOnly)
        layer = dataset.GetLayer ()
        name = layer.GetName ()
        
        return name 
        
    def rasterize (self):
        ''' perform the rasterization '''
        
        for f in self.FileList:
            layerName = self.getLayerName (f)
            
            name, _extension = os.path.splitext (f)
            outputName = name + self.OUTPUT_EXT
           
            baseImage = "{0}19_17crops-s8.tif".format (os.path.basename (name))
            baseImage = os.path.join (self.BasePath, baseImage)
            
            ds = gdal.Open (baseImage, GC.GA_ReadOnly) 
            b1 = ds.GetRasterBand (self.DEFAULT_BAND)
            self.GeoTransform = GeoTransform (dataset = ds)
            
            xmax = self.GeoTransform.XOrig + self.GeoTransform.XStep * b1.XSize 
            ymin = self.GeoTransform.YOrig + self.GeoTransform.YStep * b1.YSize 
            xmin = self.GeoTransform.XOrig
            ymax = self.GeoTransform.YOrig 
            ds = None 
            
            cmd = self.CMD_FMT.format (inp = f, 
                                       attr = self.ColorAttribute,
                                       xstep = self.GeoTransform.XStep,
                                       ystep = self.GeoTransform.YStep,
                                       xmin = xmin,
                                       xmax = xmax,
                                       ymin = ymin,
                                       ymax = ymax,
                                       layer = layerName,
                                       out = outputName)
            
            if self.Verbose == True:
                sys.stdout.write (
                    "Processing {0: >40}\n".format (f))
                sys.stdout.flush ()
            
            status = os.system (cmd)
            if status != 0:
                sys.stderr.write ("!!! Rasterization of {0} FAILED!\n\n".format (f))
            else:
                if self.Verbose == True:
                    sys.stdout.write ("-" * 78 + "\n")
                    sys.stdout.flush ()
                    
                    
if __name__ == "__main__":
    MINIMUM_ARGS    = 2
    FILELIST_START  = 2
    BASEPATH_IDX    = 1
    
    args = sys.argv[1:]
    nArgs = len (args)
    
    if nArgs < MINIMUM_ARGS:
        sys.stderr.write (
            "\nUSAGE: [python] CLURasterizer.py base-path file1.shp [file2.shp ...]\n\n") 

    else:
        filelist = sys.argv[FILELIST_START:]
        basePath = sys.argv[BASEPATH_IDX]
        
        clur = CLURasterizer (filelist, 
#                               CLUIdentifier.ID_FIELD,
                              CLUCalculator.MAJORITY_CROP_FIELD,
                              basePath,
                              verbose = True)
        
        clur.rasterize ()