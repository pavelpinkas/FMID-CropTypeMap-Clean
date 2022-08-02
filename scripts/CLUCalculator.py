#!/usr/bin/env python3

from osgeo import gdal 
from osgeo import ogr 
from osgeo import gdalconst as GC 

import sys 
import os 
import shutil
import datetime 

from scipy import stats

from GeoTransform import GeoTransform
from CLUIdentifier import CLUIdentifier

from collections import namedtuple

class CLUCalculator:
    ''' calculates zonal statistics for CLU in the region '''
    
    DEFAULT_BAND                = 1
    
    NO_COVERAGE                 = 0.00
    NO_CROP                     = 0
    
    MAJORITY_CROP_FIELD         = "MajorCrop"
    COVERAGE_FIELD              = "Coverage"
    
    def __init__ (self, items2process, outpath, verbose = False, limit = None):
        ''' constructor 
        
            @param items2process: all items to process as (map, clu) pairs 
            @param outpath: path where results will be saved '''
        
        self.Items = items2process
        self.OutputPath = outpath
        self.Verbose = verbose
        self.Limit = limit
        
        if os.path.exists (self.OutputPath):
            shutil.rmtree (self.OutputPath)
            
        os.makedirs (self.OutputPath)
        
    def getPixelData (self, south, west, north, east, transform, band):
        ''' read data for given geographical rectangle from a raster band 
        
            @param south: southern edge 
            @param north: northern edge 
            @param west: western edge 
            @param east: eastern edge 
            @param transform: geographical transformation 
            @param band: raster band with data 
            @return: 2D array of pixel data '''
        
        limX = band.XSize - 1 
        limY = band.YSize - 1
        
        pxS = transform.lat2row (south)
        pxN = transform.lat2row (north)
        pxW = transform.lon2col (west)
        pxE = transform.lon2col (east)
        
        if pxS != int (pxS): pxS += 1   # include partial pixels 
        if pxE != int (pxE): pxE += 1
        
        pxS = int (pxS)
        pxN = int (pxN)
        pxW = int (pxW)
        pxE = int (pxE)
        
        if pxN < 0: pxN = 0             # limit data cutout to within the image
        if pxS > limY: pxS = limY
        if pxW < 0: pxW = 0
        if pxE > limX: pxE = limX
        
        dataWidth = pxE - pxW + 1
        dataHeight = pxS - pxN + 1 
        
        if dataWidth < 0 or dataHeight < 0:
            result = None
        else:
            result = band.ReadAsArray (pxW, pxN, dataWidth, dataHeight)

        return result
        
    def process1 (self, datamap, clulist, clumap):
        ''' process one pixelmap against one CLU list 
        
            @param datamap: pixel map of data 
            @param clulist: list of CLUs
            @param clumap: map of CLUs
            @return: results as {CLU_ID : (majority_crop, field_coverage)}  '''
        
        state = os.path.basename (datamap)[0:2]
        state = state.upper ()
        
        cluListing = ogr.Open (clulist, GC.GA_ReadOnly)
        dataSet = gdal.Open (datamap, GC.GA_ReadOnly)
        cluSet = gdal.Open (clumap, GC.GA_ReadOnly)
        
        datGeoTransform = GeoTransform (dataset = dataSet)
        cluGeoTransform = GeoTransform (dataset = cluSet)
        
        cluBand = cluSet.GetRasterBand (self.DEFAULT_BAND)
        datBand = dataSet.GetRasterBand (self.DEFAULT_BAND)
        
        ResultRecord = namedtuple ("ResultRecord", "majorityCrop fieldCoverage")
        result = {}
        
        iCLU = 0
        
        cluVectorLayer = cluListing.GetLayer ()
        nCLUs = cluVectorLayer.GetFeatureCount ()
        for clu in cluVectorLayer:
            geom = clu.GetGeometryRef ()
            
            iCLU += 1
            if iCLU % 1000 == 0:
                txt = "{0} -> {1: >8} of {2: >8}\n".format (state, iCLU, nCLUs)
                sys.stdout.write (txt)

            if self.Limit is not None and iCLU > self.Limit:
                break
            
            if geom is not None:
                gType = geom.GetGeometryType ()
                
                fieldCoverage = None 
                majorityCrop = None
                cluID = None
                
                if gType == ogr.wkbPolygon or gType == ogr.wkbMultiPolygon:
                    envelope = geom.GetEnvelope ()
                    w, e, s, n = envelope 
                    
                    cluData = self.getPixelData (s, w, n, e, cluGeoTransform, cluBand)
                    mapData = self.getPixelData (s, w, n, e, datGeoTransform, datBand)
                    
                    if cluData is not None and mapData is not None:
                        cluID = clu.GetField (CLUIdentifier.ID_FIELD)
                        cluPixels = cluData[cluData == cluID].size 
                        
                        if cluPixels > 0:
                            validData = mapData[cluData == cluID]
#                             validData = validData[validData != self.NO_CROP]
                            validPixels = validData.size 
                            
                            if validPixels > 0:
                                fieldCoverage = validPixels / cluPixels * 100. 
                                majorityCrop = stats.mode (validData).mode[0]
                                
                    if fieldCoverage is None: fieldCoverage = self.NO_COVERAGE
                    if majorityCrop is None: majorityCrop = self.NO_CROP
                    
                    if cluID is not None:                        
                        result[cluID] = ResultRecord (majorityCrop = majorityCrop,
                                                      fieldCoverage = fieldCoverage)
                    
        return result 
                    
    def createField (self, fieldName, fieldType, layer):
        ''' create a field in a given layer 
        
            @param fieldName: name of the field 
            @param fieldType: type of the field 
            @param layer: layer to create the field in
            @return: index of created field '''
        
        fieldIndex = layer.FindFieldIndex (fieldName, True)
        
        if fieldIndex < 0:
            field = ogr.FieldDefn (fieldName, fieldType)
            layer.CreateField (field)
            fieldIndex = layer.FindFieldIndex (fieldName, True)
        
        return fieldIndex 
        
    def copyShapefile (self, source, destination):
        ''' make a copy of a shapefile with all its components 
        
            @param source: shapefile to copy (named by one of its components)
            @param destination: name for the copy '''
        
        COMPONENTS = ['shx', 'shp', 'dbf', 'prj']
                
        targetPath = os.path.dirname (destination)
        targetBaseName = os.path.basename (destination)
        targetRoot, _extension = os.path.splitext (targetBaseName)
        
        for cmp in COMPONENTS:
            sourceFile, _extension = os.path.splitext (source)
            sourceFile = ".".join ([sourceFile, cmp])
            
            targetFile = ".".join ([targetRoot, cmp])
            target = os.path.join (targetPath, targetFile)
            
            shutil.copy (sourceFile, target)
             
    def writeResults (self, clulist, results):
        ''' create a copy of the CLU list and add the results to it 
        
            @param clulist: name of the CLU list (will be duplicated 
                            and enriched in the output directory)
                            
            @param results: calculation results as 
                            {ID : (majority_value, field_coverage)} dictionary '''
        
        basename = os.path.basename (clulist)
        outputName = os.path.join (self.OutputPath, basename)
        self.copyShapefile (clulist, outputName)
        
        dataset = ogr.Open (outputName, GC.GA_Update)
        layer = dataset.GetLayer ()
        
        idFieldIndex = layer.FindFieldIndex (CLUIdentifier.ID_FIELD, True)
        
        majorityFieldIndex = self.createField (self.MAJORITY_CROP_FIELD, 
                                               ogr.OFTInteger, 
                                               layer)
        
        coverageFieldIndex = self.createField (self.COVERAGE_FIELD, 
                                               ogr.OFTReal, 
                                               layer)
        
        for feature in layer: 
            fieldID = feature.GetField (idFieldIndex)
            
            if fieldID in results:
                try:
                    r = results[fieldID]
                    feature.SetField (majorityFieldIndex, int (r.majorityCrop))
                    feature.SetField (coverageFieldIndex, float (r.fieldCoverage))
                    layer.SetFeature (feature)
                except NotImplementedError:
                    pass
            
        dataset = None 
        
    def allDataExist (self, item):
        ''' check if all necessary data exist 
        
            @param item: processing item 
            @return: True is all data exists and processing can go ahead '''
        
        result = False 
        
        if os.path.exists (item.pixelmap) and \
           os.path.exists (item.clumap)   and \
           os.path.exists (item.shpfile):
            
            result = True 
            
        return result 
    
    def calculate (self):
        ''' perform the calculation ''' 
        
        for item in self.Items:
            if self.allDataExist (item):
                datamap = item.pixelmap
                clumap = item.clumap
                clulist = item.shpfile 
                
                if self.Verbose == True:
                    sys.stdout.write ("Processing {0} with {1} ...\n".format (datamap,
                                                                              clulist))
                    sys.stdout.flush ()
                
                results = self.process1 (datamap, clulist, clumap)
                self.writeResults (clulist, results)
                
                if self.Verbose == True:
                    sys.stdout.write (" [OK]\n")
            
            else: 
                if self.Verbose == True:
                    sys.stdout.write ("! Skipping {0}, missing data\n".format (item.pixelmap))
                    sys.stdout.write ("\n")
                
if __name__ == "__main__":
    REQUIRED_ARGS = 3
    
    MAP_FMT = "{0}19_17crops.tif"
    CLU_FMT = "{0}.tif"
    SHP_FMT = "{0}.shp"
    
    STATES = ["AL", "AR", "AZ", "CA", "CO", "CT", "DE", "FL", "GA", "IA",
              "ID", "IL", "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI",
              "MN", "MO", "MS", "MT", "NC", "ND", "NE", "NH", "NJ", "NM",
              "NV", "NY", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", 
              "TX", "UT", "VA", "VT", "WA", "WI", "WV", "WY" ][:25]
    start = datetime.datetime.now ()
    
    args = sys.argv[1:]
    nArgs = len (args)
    
    if nArgs == REQUIRED_ARGS:
        mapPath, cluPath, outputPath = args 
        shpPath = cluPath 
        
        allMaps = [MAP_FMT.format (state.lower ()) for state in STATES]
        allCLUs = [CLU_FMT.format (state.lower ()) for state in STATES]
        allSHPs = [SHP_FMT.format (state.lower ()) for state in STATES]
        
        maps = [os.path.join (mapPath, amp) for amp in allMaps]
        clus = [os.path.join (cluPath, clu) for clu in allCLUs]
        shps = [os.path.join (shpPath, shp) for shp in allSHPs]
        
        ProcessItem = namedtuple ("ProcessItem", "pixelmap clumap shpfile")
        
        nItems = len (maps)
        allItems = []
        
        for iItem in range (nItems):
            allItems.append (ProcessItem (pixelmap = maps[iItem],
                                          clumap = clus[iItem],
                                          shpfile = shps[iItem]))
                                                      
        cluc = CLUCalculator (allItems, outputPath, verbose = True)
        cluc.calculate ()
        
        end = datetime.datetime.now ()
        sys.stdout.write ("\n\nProcessing took {0}\n\n".format (str (end - start)))
        
    else:
        sys.stderr.write ("\nUSAGE: [python] CLUCalculator.py map-path clu-path output-path\n\n")
        
        