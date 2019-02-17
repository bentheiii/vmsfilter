# VMS filter
## setting up the environment
install a python environment of version 3.7 or higher. The environment needs the following external dependencies:

* Gdal/OGR for python
* [websockets](https://websockets.readthedocs.io/en/stable/api.html)
   
I recommend installing [QGIS](https://qgis.org/en/site) / [osgeo4w](https://trac.osgeo.org/osgeo4w/)'s python environment, and installing websockets on it with pip. You can easily access QGIS's python's shell with `shell_qgis3.bat` written in [this repo](https://github.com/talos-gis/osgeo4w_pycharm).
## running the program
Run the file `reciever.py`. the program requires the following arguments (also listable with the `-h` option):
```
-s HOSTILE_AREAS      path for vector file with hostile areas polygons
-b HABITAT_AREAS      path for vector file with habitat areas polygons
-g IGNORE_AREAS       path for vector file with ignore areas polygons
-e EYES_WS_PATH       websocket path to the eyes server (without the /vms/... path)
-t TARGETER_TCP_IP    tcp ip of the targeter server
-p TARGETER_TCP_PORT  tcp port of the targeter server
```

All "areas" parameter can be of any OGR-compatible type.