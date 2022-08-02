from typing import Union

from osgeo import gdalconst as GConst 
from osgeo import gdal

class RasterUtils:
    ''' various common operations on raster maps ''' 

    @classmethod 
    def undeclareNoDataValue (clss, inputfile: str,
                                    replacement: Union[int, float, None] = None):

        ''' remove no data delcaration from raster and optionally replace
            all no-data pixels with a fixed value 

            @param inputfile: raster to operate on (the result will overwrite input)
            @param replacement: replacement for no-data value '''

        ds = gdal.Open (inputfile, GConst.GA_Update)

        for iBand in range (1, ds.RasterCount + 1):
            band = ds.GetRasterBand (iBand)
            
            if (ndv := band.GetNoDataValue ()) is not None:
                band.DeleteNoDataValue ()

            if replacement is not None and ndv is not None:
                data = band.ReadAsArray ()
                data[data == ndv] = replacement
                band.WriteArray (data)

        ds = None

        
