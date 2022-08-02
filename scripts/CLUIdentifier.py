#!/usr/bin/env python3

from osgeo import ogr 
from osgeo import gdalconst as GC 

import sys
import os 

class CLUIdentifier:
    ''' adds a unique ID to each CLU in the collection of CLUs '''

    ID_FIELD = "ID"
    
    def __init__ (self, clufiles, verbose = False):
        ''' constructor 
        
            @param clufile: list of CLU files '''
        
        self.CLUFiles = clufiles 
        self.UniqueID = 1
        self.Verbose = verbose
        
    def run (self):
        ''' run the identification '''
        
        for f in self.CLUFiles: 
            if os.path.exists (f):
                if not self.identifiedAlready (f):
                    if self.Verbose == True:
                        sys.stdout.write (
                            "Processing {0} (IDs from {1: >10}) ...".format (f, self.UniqueID))
                        sys.stdout.flush ()
                        
                    self.identify (f)
                    
                    if self.Verbose == True:
                        sys.stdout.write (" [DONE]\n")
                        sys.stdout.flush ()

            else:
                sys.stderr.write (f" ! CLU file does not exists {f}\n")

    def identifiedAlready (self, filename: str) -> bool:
        ''' returns true if the CLUs are already identified (ID_FIELD present) 

            @param filename: file to check 
            @return: True if identifying information already exists, False otherwise '''

        result = False 

        ds = ogr.Open (filename, GC.GA_ReadOnly)
        layer = ds.GetLayer () 
        ldef = layer.GetLayerDefn ()
        nFields = ldef.GetFieldCount ()

        for iField in range (nFields):
            fdef = ldef.GetFieldDefn (iField)
            if fdef.GetName () == self.ID_FIELD:
                result = True 
                break

        ds = None 

        return result 

    def identify (self, filename):
        ''' run the identification on a single file
            
            NOTE: if the file already contains ID field, the values 
                  of this field will be overwritten
        
            @param filename: file to process '''
                
        dataset = ogr.Open (filename, GC.GA_Update)
        layer = dataset.GetLayer ()
        
        if layer.FindFieldIndex (self.ID_FIELD, True) < 0:  # ID field does not exist yet
            idField = ogr.FieldDefn (self.ID_FIELD, ogr.OFTInteger)
            layer.CreateField (idField)
            
        idFieldIndex = layer.FindFieldIndex (self.ID_FIELD, True)
        
        for feature in layer:
            feature.SetField (idFieldIndex, self.UniqueID)
            layer.SetFeature (feature)
            self.UniqueID += 1 
        
        dataset = None 
        
if __name__ == "__main__":
    args = sys.argv[1:]
    
    if len (args) == 0:
        sys.stdout.write (
            "\nUSAGE: [python] CLUIdentifier.py file1.shp [file2.shp ...]\n\n")
        
    else:
        cluid = CLUIdentifier (args, verbose = True)
        cluid.run ()
    
            
        