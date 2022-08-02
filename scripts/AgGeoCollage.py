import sys 

from typing import List 

from ProcessRegion import ProcessRegion
from Utils.TmpFileUtils import TmpFileUtils

class AgGeoCollage:
    ''' top level driver for creating aggregated collages '''

    def __init__ (self, datapath: str, 
                        clupath: str,
                        workdir: str):
        ''' initializer 
        
            @param clupath: where the CLU files are
            @param datapath: where the basemaps are
            @param workdir: where the temporary files go '''

        self.DataPath = datapath
        self.CLUPath = clupath 
        self.WorkDir = workdir 

    def run (self, regions: List[str]): 
        ''' perform full run '''

        for region in regions: 
            prg = ProcessRegion (region,
                                 datapath = self.DataPath,
                                 clupath = self.CLUPath,
                                 workpath = self.WorkDir,
                                 mcqfilter = False,
                                 mapfmt ="{region}2021.tif")

            prg.process ()
            prg.store ()

    @classmethod 
    def printUsage (clss):
        ''' print the help text on the usage of this app '''

        sys.stderr.write ("\nUSAGE: [python3] {app} datapath clupath \n\n")

# ................................... MAIN ..................................

import os

if __name__ == "__main__":
    
    if len (sys.argv[1:]) == 0:
        AgGeoCollage.printUsage ()

    else:
        TmpFileUtils.init (prefix = "ctm2020_", suffix = ".ag")

        REGIONS = ["AR", "KS", "KY", "MD", 
                   "MN", "MO", "NC", "NJ", 
                   "TN", "VA", "WA", "WI", 
                   "WV"]

        # REGIONS = ["ar", "co", "ga", "ia", "id", "il", "in", "ks", "ky",
        #            "la", "md", "mi", "mn", "mo", "ms", "mt", "nc", "nd", "ne",
        #            "ny", "oh", "ok", "pa", "sc", "sd", "tn", "tx", "va", "wa",
        #            "wi", "al"]

        args = sys.argv[1:]
        nArgs = len (args) 
        datapath, clupath = args 

        workdir = os.path.join (os.path.dirname (datapath), "workdir")
        agc = AgGeoCollage (datapath, clupath, workdir)
        agc.run (REGIONS)

        TmpFileUtils.cleanup ()