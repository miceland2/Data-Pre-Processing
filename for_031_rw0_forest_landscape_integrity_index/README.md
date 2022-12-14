## Forest Landscape Integrity Index Dataset Pre-processing
This file describes the data pre-processing that was done to the [Forest Landscape Integrity Index](https://www.forestintegrity.com/) for [display on Resource Watch](https://resourcewatch.org/data/explore/e044a0d7-b3d4-4612-9848-71322b1772cc).

This dataset is provided by the source as a GeoTIFF file. The following variable is shown on Resource Watch:
- 2019 Forest Landscape Integrity Index (flii): Continuous index representing the degree of forest anthropogenic modification for the beginning of 2019 
 
The data source multiplied the data by 1000 to store values in Integer format. Data was divided by 1000 to obtain proper values (Range 0-10) for display on Resource Watch.

Please see the [Python script](https://github.com/resource-watch/data-pre-processing/blob/master/for_031_rw0_forest_landscape_integrity_index/for_031_rw0_forest_landscape_integrity_index_processing.py) for more details on this processing.

You can view the processed dataset for [display on Resource Watch](https://resourcewatch.org/data/explore/e044a0d7-b3d4-4612-9848-71322b1772cc).

You can also download the original dataset [from the source website](https://www.forestintegrity.com/download-data).

###### Note: This dataset processing was done by [Rachel Thoms](https://www.wri.org/profile/rachel-thoms) and QC'd by [Yujing Wu](https://www.wri.org/profile/yujing-wu).
