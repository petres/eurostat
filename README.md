## eurostat bulk exporter
### About
This program provides a graphical user interface (GUI) which allows [bulk datasets](http://epp.eurostat.ec.europa.eu/portal/page/portal/statistics/bulk_download) downloads from [eurostat](http://epp.eurostat.ec.europa.eu/). The downloaded datasets can be filtered, sorted and exported to Excel files. Other export file types will follow (CSV, STATA datasets, R datasets, ...). 
In addition presets can be created, stored and executed which helps to automize recurring eurostat data exports. It also allows the automatic creation of charts in Excel files.

#### Screenshot
![Screenshot](https://raw.githubusercontent.com/petres/eurostat/gh-pages/mainOverview.png)

#### Dependencies
* [Python](https://www.python.org/) > 2.6  (should also work with version 3) | Programming Language
* [PyQt](http://www.riverbankcomputing.com/software/pyqt) 4 | GUI 
* [openpyxl](http://openpyxl.readthedocs.org/) | Writing Excel Files (in this repo)

It's working fine with [Portable Python](http://portablepython.com/) (2.7.6.1). 

#### Submodule Libraries
* [simplejson](http://simplejson.readthedocs.org/) | Writing/Reading JSON

___
### Wiki
If you want to know more about planned features or need a description please read the [Wiki page](http://github.com/petres/eurostat/wiki) of this project.

___

### Get it
#### GIT
Some libraries are included via submodules, therefore the repo has either to be cloned recursively with 
`git clone --recursive https://github.com/petres/eurostat` 
or the submodules have to be initialized with the command 
`git submodule update --init`. 

#### Compressed Files
In the near future we will provide `zip` and `tar.gz` files.

#### Executables
Maybe at some point in the unknown future.

___

### Run it
#### Windows
1.  Adjust the paths in the `app\utils\config.bat` file.
1.  Convert the `*.ui` files with the script `app\utils\convertUI.bat`.
1.  Call `run.bat`.

If your are using Portable Python the paths should look like:
```Batchfile
set python = "D:\some\where\Portable Python\App\python.exe"
set pyuic  = "D:\some\where\Portable Python\App\Lib\site-packages\PyQt4\uic\pyuic.py"
```

#### Linux
It is assumed that `python` and `pyuic4` are in your `PATH` environment variable and `make` build utility is installed.

1.  Convert the `*.ui` files by running `make` in the `app/` path.
1.  Call `./run.sh`.
