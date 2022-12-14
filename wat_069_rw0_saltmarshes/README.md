## Saltmarshes Dataset Pre-processing
This file describes the data pre-processing that was done to [the Global Distribution of Saltmarshes](https://data.unep-wcmc.org/datasets/43%20(v.6)) for [display on Resource Watch](https://resourcewatch.org/data/explore/6a22c67d-9e3c-4f8c-94d2-d90fe886b476).

The source provided this dataset as two shapefiles - one of which contains polygon data, and the other contains point data. Resource Watch only displays the polygon layer.

Below, we describe the steps used to reformat the polygon shapefile:
1. Read in the polygon shapefile as a geopandas data frame.
2. Convert the data type of column 'METADATA_I' to integer.
3. Convert the column names to lowercase so the table can be uploaded to Carto without losing information.
4. Project the data so its coordinate system is WGS84.

Please see the [Python script](https://github.com/resource-watch/data-pre-processing/blob/master/wat_069_rw0_saltmarshes/wat_069_rw0_saltmarshes_processing.py) for more details on this processing.

You can view the processed Saltmarshes dataset [on Resource Watch](https://resourcewatch.org/data/explore/6a22c67d-9e3c-4f8c-94d2-d90fe886b476).

You can also download the original dataset [directly through Resource Watch](http://wri-public-data.s3.amazonaws.com/resourcewatch/wat_069_rw0_saltmarshes.zip), or [from the source website](https://data.unep-wcmc.org/datasets/43%20(v.6)).

###### Note: This dataset processing was done by [Rachel Thoms](https://www.wri.org/profile/rachel-thoms), and QC'd by [Yujing Wu](https://www.wri.org/profile/yujing-wu).
