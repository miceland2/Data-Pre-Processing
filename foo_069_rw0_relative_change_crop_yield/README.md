## Relative Change in Crop Yield Dataset Pre-processing
This file describes the data pre-processing that was done to [Relative change in crop yield](http://climate-impact-explorer.climateanalytics.org/).

The data was retrieved from the Climate Analytics' Impact Data Explorer API, which provides a CSV file for each administrative unit (e.g, country or province).

Below, we describe the steps used to combine CSVs for each country/province into one global table on Carto.

1. Loop through CSVs and append a country column that adds the ISO3 code.
2. Loop through CSVs and append a provincial column that adds the admin1 code. 
3. Create a Pandas dataframe for each CSV.
4. Combine all the newly created dataframes together into one dataframe. 
5. Create a new column 'datetime' to store years as datetime objects.
6. Drop the unnamed column.
7. Filter out CAT emissions scenario columns.
8. Filter out NGFS emissions scenario columns.
9. Replace periods in column headers with underscores.
10. Replace whitespaces with underscores in column headers.
11. Replace NaN with None.
12. Save Processed dataframe as a CSV.

Please see the [Python script](https://github.com/resource-watch/data-pre-processing/blob/master/foo_069_rw0_relative_change_crop_yield/foo_069_rw0_relative_change_crop_yield_processing.py) for more details on this processing.

You can also download the original dataset [directly through Resource Watch](https://wri-public-data.s3.amazonaws.com/resourcewatch/foo_069_rw0_relative_change_crop_yield.zip), or [from the source website](https://cie-api.climateanalytics.org/api/).

###### Note: This dataset processing was done by [Alex Sweeney](https://github.com/alxswny) and [Weiqi Zhou](https://www.wri.org/profile/weiqi-zhou), and QC'd by [Chris Rowe](https://www.wri.org/profile/chris-rowe).
