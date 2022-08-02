#!/usr/bin/env python3 

from typing import Union, Dict, Any

import sys

from Reprojector import Reprojector
from GeoTransform import GeoTransform

from Utils.UnitUtils import UnitUtils
from Utils.TmpFileUtils import TmpFileUtils

from osgeo import gdalconst as GConst  
from osgeo import gdal 

import numpy as NPy

class BeanCounter2:
    ''' analyzes the effect of filtering on the data ''' 

    WORK_PROJ4      = "+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs"

    INPUTS          = [(RAW      := "raw"),
                       (CLEAN    := "clean"),
                       (PRODUCT  := "product")]

    TOTAL           = "sum"
    REGION_TOTAL    = "TOTAL"

    TAreaDists = Dict[int, float]
    TSingleResult = Dict[str, TAreaDists] 
    TResultDict = Dict[str, TSingleResult]

    CROP_NAMES      = {0 : "UCULTIV",
                       1 : "WHEAT",
                       2 : "CORN",
                       3 : "SOYBEAN",
                       4 : "UCOTTON",
                       5 : "OTHER",
                       6 : "PREVENT",
                       7 : "SORGHUM",
                       8 : "RICE"}

    def __init__ (self, output: str):
        ''' initializer 
        
            @param output: where to write the results ''' 

        self.Results: Dict[Any, Any] = {} # TResultDict
        self.Output = output
        
        if os.path.exists (self.Output):
            os.unlink (self.Output)

    def analyze (self, *, region: str,
                          raw: str,
                          clean: str,
                          product: str):

        ''' analyzes a single run, making comparison between  the following files:
        
            @param region: region name for identification 
            @param raw: initial data with no cleanup applied 
            @param clean: data after application of the DeNoise filter
            @param product: final data, after reprojection '''

        areaDist: Dict[Any, Any] = {} # TSingleResult 
        
        inputFiles = {self.RAW     : raw,
                      self.CLEAN   : clean,
                      self.PRODUCT : product}

        for part in self.INPUTS:
            areaDist[part] = self.calculateAreaDists (inputFiles[part])

        self.Results[region] = areaDist

    def calculateAreaDists (self, filename: str) -> TAreaDists:
        ''' calculate area distributions by crop type 

            @param filename: file to analyze 
            @return: area distributions '''

        result: Dict[Any, Any] = {} # TAreaDists

        if (prj := Reprojector.p4Projection (filename)) != self.WORK_PROJ4:
            workmap = TmpFileUtils.newTmp (filename)
            Reprojector ().warpRaster (filename, workmap, self.WORK_PROJ4)
        else:
            workmap = filename

        ds = gdal.Open (workmap, GConst.GA_ReadOnly)
        band = ds.GetRasterBand (1)
        noDataValue = band.GetNoDataValue ()
        data = band.ReadAsArray ()

        gtrans = GeoTransform (dataset = ds)
        pixelArea = gtrans.getPixelArea ()
        pixelArea = UnitUtils.acres (meters = pixelArea) 

        types, counts = NPy.unique (data, return_counts = True)
        nTypes = len (types)

        for iType in range (nTypes):
            if noDataValue is None or types[iType] != noDataValue:
                result[types[iType]] = counts[iType] * pixelArea

        ds = None 
        if workmap != filename:
            os.unlink (workmap)

        return result 

    def report (self):
        ''' print the report of all recorded results ''' 

        self.homogenizeReports ()
        self.summarizeReports ()

        for region in self.Results:
            result = self.Results[region]
            self.reportAreas (result, region)

        self.reportAreas (self.Summaries, self.REGION_TOTAL)

        for region in self.Results:
            result = self.Results[region] 
            self.reportPercentages (result, region)

        self.reportPercentages (self.Summaries, self.REGION_TOTAL)

    def summarizeReports (self):
        ''' calculate the summary reports ''' 

        self.Summaries = {}

        for reportType in self.INPUTS:
            self.Summaries[reportType] = {}

            for key in self.AllKeys:
                self.Summaries[reportType][key] = 0
                    
                for region in self.Results:
                    self.Summaries[reportType][key] += self.Results[region][reportType][key]

    def homogenizeReports (self):
        ''' prepare summary report and add it to the results '''

        self.AllKeys = []

        for region in self.Results:
            regionData = self.Results[region]

            for reportType in regionData:
                data = regionData[reportType]

                for cropType in data:
                    if cropType not in self.AllKeys:
                        self.AllKeys.append (cropType)

        for region in self.Results:
            regionData = self.Results[region]

            for reportType in regionData:
                data = regionData[reportType]

                for cropType in self.AllKeys:
                    if cropType not in data:
                        data[cropType] = 0

    def reportPercentages (self, result: TSingleResult, region: str):
        ''' make the report but use percentages against raw data 

            @param result: result to report 
            @param region: region identifier '''

        outf = open (self.Output, "a")
    
        HEADER_FMT  = "{region: <8}         RAW    CLEAN  PRODUCT"
        DATA_FMT    = "        {ctype: <8} {raw: >6.2f} {clean: >6.2f} {product: >6.2f}\n" 
        SINGLE_FMT  = "{0: >6.2f}"
        ERROR_FMT   = "{0: >6}"
        DATAROW_FMT = "     {code: >2} {ctype: <8} {raw} {clean} {product}\n"
        
        header = HEADER_FMT.format (region = region)
        uline = "-" * len (header)
        header = "\n".join ((uline, header, uline)) + "\n"
        outf.write (header)

        for rk in self.AllKeys:
            fmtf = lambda x: SINGLE_FMT.format (x) if x is not None else ERROR_FMT.format ("!!!")

            base = result[self.RAW][rk]
            rawp = fmtf (self.perc (result[self.RAW][rk], base))
            cleanp = fmtf (self.perc (result[self.CLEAN][rk], base))
            productp = fmtf (self.perc (result[self.PRODUCT][rk], base))

            datarow = DATAROW_FMT.format (ctype = self.CROP_NAMES[rk],
                                          raw = rawp,
                                          clean = cleanp,
                                          product = productp,
                                          code = rk)
            outf.write (datarow)

        outf.write ('\n')
        outf.close ()

    def perc (self, value: float, base: float) -> Union[None, float]:
        ''' calculate percentage vs. given base 

            @param value: values to scale 
            @param base: base (100%)
            @return: percentage of the value with the respect to the base '''

        result: Union[None, float]

        if base != 0:
            result = value / base * 100.
            if result > 999: result = None
        else:
            result = 0.00

        return result 

    def reportAreas (self, result: TSingleResult, region: str):
        ''' print the area report for single result 
        
            @param result: result data 
            @param region: region where the data were calculated ''' 

        outf = open (self.Output, "a")

        HEADER_FMT = "{region: <6}            RAW         CLEAN       PRODUCT     "
        DATA_FMT   = "      {code: <2} {ctype: <8} {raw: >11.2f} {clean: >11.2f} {product: >11.2f}\n"
        
        header = HEADER_FMT.format (region = region)
        uline = "-" * len (header)
        header = "\n".join ((uline, header, uline)) + "\n"
        outf.write (header)

        for rk in self.AllKeys:
            datarow = DATA_FMT.format (ctype = self.CROP_NAMES[rk],
                                       raw = result[self.RAW][rk],
                                       clean = result[self.CLEAN][rk],
                                       product = result[self.PRODUCT][rk],
                                       code = rk)
            outf.write (datarow)

        outf.write ("\n")
        outf.close ()

# ..................................... MAIN ................................

import os 

if __name__ == "__main__":

    REQUIRED_ARGS = 3

    args = sys.argv[1:]
    nArgs = len (args)

    if nArgs == REQUIRED_ARGS:
        RAW_DATA_FMT = "{ubase}2020_20200711.tif"
        BASE_DATA_FMT = "{lbase}.tif"

        with TmpFileUtils () as _tmpfu:
            dataPath, productPath, output = sys.argv[1:]
            bc = BeanCounter2 (output)   

            subdirs = sorted (os.listdir (productPath))
            for sd in subdirs[:]:
                if sd != "OH":
                    continue 
                
                base = os.path.basename (sd)
                lbase = base.lower ()
                ubase = base.upper ()
                raw = RAW_DATA_FMT.format (ubase = ubase)
                dtf = BASE_DATA_FMT.format (lbase = lbase)

                pDir = os.path.join (productPath, sd)

                bc.analyze (region = base, 
                            raw = os.path.join (dataPath, raw),
                            clean = os.path.join (pDir, BeanCounter2.CLEAN, dtf),
                            product = os.path.join (pDir, BeanCounter2.PRODUCT, dtf))

            bc.report ()

    else:
        app = os.path.basename (sys.argv[0])
        sys.stderr.write (f"\nUSAGE: [python3] {app} datapath productdir\n\n")      