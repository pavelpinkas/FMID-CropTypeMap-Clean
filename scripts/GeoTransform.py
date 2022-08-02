from osgeo import gdal
from osgeo import gdalconst as GC 

import math 

class GeoTransform:
    ''' helper class to transform between pixel and geographical coordinate systems ''' 
     
    FMT = "X :: {0:+13.8f}/{1:+13.10f}; Y :: {2:+13.8f}/{3:+13.10f}"
    
    def __init__ (self, datafile = None, dataset = None):
        ''' constructor 
        
            @param datafile: file to extract geo-transfomration from 
            @param dataset: dataset to extract geo-transformation from (if already open) '''
                    
        self.Dataset = gdal.Open (datafile, GC.GA_ReadOnly) if dataset is None else dataset
        
        (self.XOrig,
        self.XStep,
        _xrot,
        self.YOrig,
        _yrot,
        self.YStep) = self.Dataset.GetGeoTransform ()
        
        if dataset is None:      # if we opened the dataset here, 
            self.Dataset = None  # close it, we don't need it anymore, otherwise leave it alone
        
    def getPixelArea (self):
        ''' return area of an pixel, in whatever units the transformation is in '''

        return math.fabs (self.XStep * self.YStep)

    def pixelCoords (self, latitude, longitude):
        ''' convert longitude -> x and latitude -> y 
        
            @param latitude: latitude 
            @param longitude: longitude 
            @return x and y for pixel position '''
        
        x = self.lon2col (longitude) 
        y = self.lat2row (latitude) 
        
        return x, y 
    
    def geoCoords (self, x, y):
        ''' convert x -> longitude and y -> latitude 
        
            @param x: x-coordinate of the pixel
            @param y: y-coordinate of the pixel 
            @return: latitude and longitude, in that order '''
        
        latitude = self.row2lat (y)
        longitude = self.col2lon (x)
        
        return latitude, longitude 
    
    def lat2row (self, latitude):
        ''' convert latitude -> row 
        
            @param latitude: latitude to convert 
            @return: row index '''
        
        return (latitude - self.YOrig) / self.YStep
    
    def lon2col (self, longitude):
        ''' convert longitude -> column 
        
            @param longitude: longitude to convert 
            @return: column index '''
        
        return (longitude - self.XOrig) / self.XStep 
     
    def row2lat (self, row):
        ''' convert row -> latitude 
        
            @param row: row index 
            @return: latitude '''
        
        return self.YOrig + self.YStep * row  
    
    def col2lon (self, col):
        ''' convert column -> longitude 
        
            @param col: column index 
            @return: longitude '''
        
        return self.XOrig + self.XStep * col 

    def __str__ (self):
        ''' stringify 
        
            @return: string representation''' 
        
        return self.FMT.format (self.XOrig, 
                                self.XStep,
                                self.YOrig, 
                                self.YStep)
        
    def __repr__ (self):
        ''' stringify 
        
            @return: string representation '''
        
        return self.__str__ ()
    