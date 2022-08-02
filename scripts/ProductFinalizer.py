import os 

class ProductFinalizer:
    ''' performs final reprojection and scaling '''

    DEFAULT_XRES            = 10
    DEFAULT_YRES            = 10
    DEFAULT_PROJECTION      = "+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs"
    DEFAULT_OPTIONS         = "-co COMPRESS=LZW -co TILED=YES -r near -q"

    CMD_FMT                 = 'gdalwarp -tr {xres} {yres} -t_srs "{proj}" {opts} {inp} {out}'

    def __init__ (self, *, source: str, 
                           product: str,
                           xres: float = DEFAULT_XRES,
                           yres: float = DEFAULT_YRES,
                           options: str = DEFAULT_OPTIONS,
                           proj4: str = DEFAULT_PROJECTION):

        ''' initializer 

            @param source: source image 
            @param product: final product 
            @param xres: X-resolution
            @param yres: Y-resolution 
            @param options: additional processing options 
            @param proj4: target projection string ''' 

        self.Source = source 
        self.Product = product 
        self.XRes = xres
        self.YRes = yres
        self.Options = options
        self.Projection = proj4

    def process (self):
        ''' perform the final production steps '''

        if os.path.exists (self.Product):
            os.unlink (self.Product)

        cmd = self.CMD_FMT.format (xres = self.XRes, 
                                   yres = self.YRes,
                                   inp = self.Source,
                                   out = self.Product,
                                   proj = self.Projection,
                                   opts = self.Options)

        os.system (cmd)

# ................................. MAIN ....................................

import sys 
import os 
import glob 

if __name__ == "__main__":

    REQUIRED_ARGS = 2

    args = sys.argv[1:]
    nArgs = len (args)

    if nArgs == REQUIRED_ARGS:
        inpdir, outdir = args 
        fpattern = os.path.join (inpdir, "*.tif")
        files = glob.glob (fpattern)

        for f in files:
            product = os.path.join (outdir, os.path.basename (f))
            pf = ProductFinalizer (source = f, product = product)
            pf.process ()

    else:
        app = os.path.basename (sys.argv[0])
        sys.stderr.write (f"\nUSAGE: [python3] {app} inpdir outdir\n\n")