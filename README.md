## eurostat bulk exporter

### About

This program provides a graphical user interface (GUI) which allows [bulk datasets](http://epp.eurostat.ec.europa.eu/portal/page/portal/statistics/bulk_download) downloads from [eurostat](http://epp.eurostat.ec.europa.eu/). The downloaded datasets can be filtered, sorted and exported to Excel files. Other export file types will follow (csv, ...). In addition presets can be created, stored and executed which help to automize recurring eurostat data exports.

__Dependencies__

* Python (version > 2.6, should also work with version 3)
* PyQt4
* [xlwt](http://www.python-excel.org/) (still in this repository)

It's working fine with [Portable Python](http://portablepython.com/) (2.7.6.1). 

### Run it
__Windows__

1.  Adjust the paths in the `app\utils\config.bat` file.
1.  Convert the `*.ui` files with the script `app\utils\convertUI.bat`.
1.  Call `app\run.bat`.

If your are using Portable Python the paths should look like:
```Batchfile
set python = "D:\some\where\Portable Python\App\python.exe"
set pyuic  = "D:\some\where\Portable Python\App\Lib\site-packages\PyQt4\uic\pyuic.py"
```

__Linux__

It is assumed that `python` and `pyuic4` are in your `PATH` environment variable and `make` build utility is installed.

1.  Convert the `*.ui` files by running `make` in the `app/` path.
1.  Call `app/run.sh`.
