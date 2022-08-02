When running the code in standard configuration, the data locations 
will be as follow:

  * The files to clean of pixel scatter and reproject go to basemaps/
  * The files cleaned of pixel scatter will be in product/??/clean
    (the ?? stands for two letter state code and (all subdirectories 
    are created automatically).
  * A working copy of each processed file will be left at product/??/raw

The ndv.sh script can be used for preprocessing the input (should they
not have `no-data-value` defined.

The stdnames.py script can be used to renaming raw files into expected 
naming scheme: ??.tf (?? being two letter US state code).
