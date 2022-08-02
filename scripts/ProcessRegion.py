#!/usr/bin/env python3 

import os 
import shutil

from collections import namedtuple

# from Utils.TmpFileUtils import TmpFileUtils
from RasterUtils import RasterUtils

from CLUIdentifier import CLUIdentifier
from CLURasterizer2 import CLURasterizer2
from CLUCalculator import CLUCalculator
from CLUResultMerge import CLUResultMerge

from PreferredValue import PreferredValue

from ProductFinalizer import ProductFinalizer
from BeanCounter import BeanCounter

from MultiColorSweep import MultiColorSweep
from CoreFill import CoreFill

from typing import Union 

from osgeo import gdalconst as GConst 
from osgeo import gdal 

class ProcessRegion: 
    ''' has all tools to process a single region (basemap + CLU) '''

    CLU_FMT                 = "{region}.shp"
    MAP_FMT                 = "{region}2021.tif"
    REG_FMT                 = "{region}.tif"

    MIN_CLUSTER_SIZE        = 7

    PRODUCT_RESOLUTION_X    = 30
    PRODUCT_RESOLUTION_Y    = 30

    NO_VALUE_REPLACEMENT    = 0

    def __init__ (self, region: str, 
                        datapath: str, 
                        clupath: str, 
                        workpath: str,
                        mcqfilter: bool = True, 
                        dataskew: BeanCounter = None,
                        clufmt: str = CLU_FMT,
                        mapfmt: str = MAP_FMT,
                        regionfmt: str = REG_FMT):


        ''' initializer 

            @param region: region name 
            @param clupath: where the CLU data are 
            @param datapath: where the pixel data are 
            @param workpath: where the intermediate files go
            @param dataskew: if not None, run the dataskew analysis 
            @param clufmt: filename format for CLUs 
            @param mapfmt: filename format for basemaps 
            @paraself.TAreaDistsm regionfmt: filename format for regions '''

        self.CluFormat = clufmt
        self.RegionFormat = regionfmt
        self.MapFormat = mapfmt 

        self.CLUFile = self.CluFormat.format (region = region.lower ())
        self.CLUFile = os.path.join (clupath, self.CLUFile)

        self.DataSkewAnalyzer = dataskew

        self.MapFile = self.MapFormat.format (region = region.upper ())
        self.MapFile = os.path.join (datapath, self.MapFile)

        self.CLUPath= clupath
        self.DataPath = datapath
        self.WorkPath = workpath

        self.Region = region

        workParent = os.path.dirname (self.WorkPath)
        self.WorkParent = workParent

        self.ResultPath = os.path.join (workParent, "results") 
        self.CleanMapPath = os.path.join (workParent, "clean")
        self.ProductPath = os.path.join (workParent, "product")
        self.SweptMapPath = os.path.join (workParent, "swept")
        self.MergePath = os.path.join (workParent, "merged")
        self.AdjustedPath = os.path.join (workParent, "adjusted")

        self.MCQFilterUse = mcqfilter

        for dirpath in [self.WorkPath, 
                        self.ResultPath, 
                        self.CleanMapPath,
                        self.ProductPath,
                        self.SweptMapPath,
                        self.MergePath,
                        self.AdjustedPath]:

            if os.path.exists (dirpath):
                shutil.rmtree (dirpath)

            os.makedirs (dirpath)

    def getNoDataValue (self) -> Union[int, float]:
        ''' find out what is no-data value for this particular basemap '''

        ds = gdal.Open (self.MapFile, GConst.GA_ReadOnly)
        b1 = ds.GetRasterBand (1)
        noDataValue = b1.GetNoDataValue () 

        return noDataValue 

    def setNoDataValue (self, dataset: str):
        ''' sets the current NoDataValue as such to a given dataset ''' 

        ds = gdal.Open (dataset, GConst.GA_Update)
        for idx in range (ds.RasterCount):
            iBand = idx + 1
            band = ds.GetRasterBand (iBand)
            band.SetNoDataValue (self.NoDataValue)

        ds = None 

    def process (self): 
        ''' perform the processing '''

        self.NoDataValue = self.getNoDataValue ()
        hasCLUs = os.path.exists (self.CLUFile)

        if hasCLUs:
            self.identifyCLUs ()
            self.rasterizeCLUs ()
            self.aggregateCLUs ()
            self.rasterizeAggregate ()
            self.scatterCleanup ()
            self.resultMerge ()
        else:
            self.scatterCleanup ()

            mapName = self.baseMapName ()
            sweptMap = os.path.join (self.SweptMapPath, mapName)
            self.MergedMap = os.path.join (self.MergePath, mapName)
            
            shutil.copy (sweptMap, self.MergedMap)

        self.finalAdjust ()
        self.finalProduct ()
        self.nvReplace (self.ProductMap, self.NO_VALUE_REPLACEMENT) 

    def finalAdjust (self):
        ''' perform the adjustment of uncultivated areas for better match 
            with reality '''

        self.AdjustedMap = os.path.join (self.AdjustedPath, 
                                         self.baseMapName ())

        pv = PreferredValue ((PRIORITY_COLOR := 0))
        pv.process (self.MergedMap, self.AdjustedMap, self.MapFile)

    def resultMerge (self):
        ''' merge the cleaned (vector based) map with the pixel data '''

        clumg = CLUResultMerge (self.CleanMapPath,
                                self.SweptMapPath,
                                self.WorkPath,
                                self.MergePath)

        clumg.merge ()

        self.MergedMap = os.path.join (self.MergePath, 
                                       self.baseMapName ())

    def baseMapName (self) -> str:
        ''' basic name for file with a map 

            return: base map name '''

        return self.RegionFormat.format (region = self.Region.lower ())

    def finalProduct (self):
        ''' finalize the product's resolution and projection '''

        mapName = self.baseMapName ()
        self.ProductMap = os.path.join (self.ProductPath, mapName)
        pf = ProductFinalizer (source = self.AdjustedMap, 
                               product = self.ProductMap,
                               xres = self.PRODUCT_RESOLUTION_X,
                               yres = self.PRODUCT_RESOLUTION_Y)
        pf.process ()

    def cleanMapName (self):
        ''' calculate the name for cleaned map 

            @return: cleaned map full path '''

        cluFile = os.path.basename (self.CLUFile)
        cluBase, _ext = os.path.splitext (cluFile)
        aggregate = os.path.join (self.ResultPath, cluFile)
        output = os.path.join (self.CleanMapPath, cluBase + ".tif")

        return output, aggregate

    def rasterizeAggregate (self):
        ''' rasterizes the aggregate to create vector based clean map '''

        output, aggregate = self.cleanMapName ()
        rasterizer = CLURasterizer2 (vectorfile = aggregate, 
                                     baseraster = self.MapFile,
                                     colorAttr = CLUCalculator.MAJORITY_CROP_FIELD,
                                     output = output,        
                                     verbose = True)

        rasterizer.rasterize ()
        self.setNoDataValue (output)

    def scatterCleanup (self):
        ''' removes smale clusters of pixels '''    

        filename = os.path.basename (self.MapFile)
        dirname = os.path.dirname (self.MapFile)
        name, ext = os.path.splitext (filename)
        
        self.MapFileClean = name[0:2].lower () + ext
        self.MapFileClean = os.path.join (self.SweptMapPath, self.MapFileClean)

        if self.MCQFilterUse == True:
            if not os.path.exists (self.MapFileClean):
                mcs = MultiColorSweep (inpFile = self.MapFile,
                                       outFile = self.MapFileClean,
                                       minSize = self.MIN_CLUSTER_SIZE,
                                       ignorenv = True)
                mcs.sweep ()

        else:
            shutil.copy (self.MapFile, self.MapFileClean)
        
    def identifyCLUs (self):
        ''' assign each CLU a unique identifier '''

        cluidr = CLUIdentifier ([self.CLUFile], verbose = True)
        cluidr.run ()

    def rasterizeCLUs (self):
        ''' create a raster map with all CLUs properyl differentiated by 
            their identifier ''' 
        
        clufile = os.path.basename (self.CLUFile)
        self.RasterizedCLUs = os.path.join (self.WorkPath, clufile)
        name, _ext = os.path.splitext (self.RasterizedCLUs)
        self.RasterizedCLUs = name + "-clu.tif"

        rasterizer = CLURasterizer2 (vectorfile = self.CLUFile, 
                                     baseraster = self.MapFile,
                                     colorAttr = CLUIdentifier.ID_FIELD,
                                     output = self.RasterizedCLUs,        
                                     verbose = True)
        rasterizer.rasterize ()

    def aggregateCLUs (self):
        ''' compute aggregates crop types for each of the CLUs '''

        ProcessItem = namedtuple ("ProcessItem", "pixelmap clumap shpfile")
        item = ProcessItem (pixelmap = self.MapFile,
                            clumap = self.RasterizedCLUs,  
                            shpfile = self.CLUFile)

        cluCalc = CLUCalculator ([item], 
                                 self.ResultPath, 
                                 verbose = True,
                                 limit = None) 
        cluCalc.calculate ()

    def store (self):
        ''' store all valuable results ''' 

        storedir = os.path.join (self.WorkParent, "production", self.Region.upper ())
        if os.path.exists (storedir):
            shutil.rmtree (storedir) 
        os.makedirs (storedir)
        
        SUBDIRS = ["clean", 
                   "merged", 
                   "product", 
                   "results", 
                   "swept", 
                   "workdir",
                   "adjusted"]
                   
        for sd in SUBDIRS:
            sourceDir = os.path.join (self.WorkParent, sd)
            targetDir = os.path.join (storedir, sd)
            os.mkdir (targetDir)
            
            files = os.listdir (sourceDir)
            for f in files:
                sourceFile = os.path.join (sourceDir, f)
                shutil.copy (sourceFile, targetDir)

    def nvReplace (self, datafile: str, replacement: Union[float, int]):
        ''' replace the no-value pixels with pixels of set value 

            @param datafile: file to operate on 
            @param replacement: replacement value for no data pixels '''

        sys.stdout.write ("Finalizing {0} ...\n".format (os.path.basename (datafile)))
        sys.stdout.flush ()
        RasterUtils.undeclareNoDataValue (datafile, replacement)

# ..................................... MAIN ................................

import sys 
import os

if __name__ == "__main__":
    
    REQUIRED_ARGUMENTS = 1
    DATAPATH = "data2/basemaps"
    CLUPATH = "data2/clus"
    WORKDIR = "data2/workdir"

    args = sys.argv[1:]
    nArgs = len (args)

    if nArgs == REQUIRED_ARGUMENTS:
        region, = args
        prg = ProcessRegion (region, datapath = DATAPATH, 
                                     clupath = CLUPATH,
                                     workpath = WORKDIR) 
        prg.process ()
    else:
        app = os.path.basename (sys.argv[0])
        sys.stderr.write ("\nUSAGE: [python3] {app} basemap clulist\n\n")
