import logging
import pandas as pd
import glob
import os
import dotenv
#insert the location of your .env file here:
dotenv.load_dotenv('/home/hastur_2021/documents/rw_github/cred/.env')
import sys
utils_path = os.path.join(os.path.abspath(os.getenv('PROCESSING_DIR')),'utils')
if utils_path not in sys.path:
    sys.path.append(utils_path)
import util_files
import util_cloud
import util_carto
import zipfile
from zipfile import ZipFile
import shutil
import datetime

# Set up logging
# Get the top-level logger object
logger = logging.getLogger()
for handler in logger.handlers: logger.removeHandler(handler)
logger.setLevel(logging.INFO)
# make it print to the console.
console = logging.StreamHandler()
logger.addHandler(console)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# name of folder script folder
# This dataset will be divided in two
dataset_name = 'foo_066_rw0_food_product_shares' #check

logger.info('Executing script for dataset: ' + dataset_name)
# create a new sub-directory within your specified dir called 'data'
# within this directory, create files to store raw and processed data
data_dir = util_files.prep_dirs(dataset_name)

'''
Download data and save to your data directory
This script process two files related to import and export product shares

Data for imports can be downloaded with the following link:
https://wits.worldbank.org/CountryProfile/en/Country/WLD/StartYear/1988/EndYear/2019/TradeFlow/Export/Indicator/XPRT-PRDCT-SHR/Partner/ALL/Product/16-24_FoodProd
Data for exports can be downloaded with the following link:
https://wits.worldbank.org/CountryProfile/en/Country/WLD/StartYear/1988/EndYear/2019/TradeFlow/Import/Indicator/MPRT-PRDCT-SHR/Partner/ALL/Product/16-24_FoodProd#

Two excel files was downloaded from the explorer
after selecting the following options from menu:
    
    Countriy/region: World
    Year: 1988-2019
    Trade flow: Import/Export
    Indicators: Import Product share(%)/Export Product share(%)
    View By: Product
    Product: Food Products
    Partner: By country and region

'''
# download the data from the source
logger.info('Downloading raw data')
downloads = []
downloads.append(glob.glob(os.path.join(os.path.expanduser("~"), 'Downloads', 'WITS-Partner-import.xlsx'))[0])
downloads.append(glob.glob(os.path.join(os.path.expanduser("~"), 'Downloads', 'WITS-Partner-export.xlsx'))[0])
# Create file paths where the excel files will be stored
raw_data_file = [os.path.join(data_dir,os.path.basename(download)) for download in downloads]
# We move the files stored in the downloads list
for index, element in enumerate(downloads):
    shutil.move(element, raw_data_file[index])

'''
Process data
'''
# We read the product import share dataset first
# Go through data directory and append xlsx files into a list
# Then concatenate the content of the list in a dataframe

df_list = []
for file in raw_data_file:
    df = pd.read_excel(file, sheet_name = 'Product-TimeSeries-Partner')
    df_list.append(df)
df = pd.concat(df_list, ignore_index=True)

# convert tables from wide form (each year is a column) to long form
df_edit = pd.melt(df,id_vars=['Reporter Name','Partner Name','Trade Flow','Product Group',
                              'Indicator'],var_name='year', value_name='share_percentage')
 

# replace spaces and special characters in column headers with '_" 
df_edit.columns = df_edit.columns.str.replace(' ', '_')
df_edit.columns = df_edit.columns.str.replace('/', '_')
df_edit.columns = df_edit.columns.str.replace('-', '_')

# replace all NaN with None
df_edit = df_edit.where((pd.notnull(df_edit)), None)

# convert the column names to lowercase
df_edit.columns = [x.lower() for x in df_edit.columns]

# convert the data type of the column 'year' to integer
df_edit['year'] = df_edit['year'].astype('int64')

# convert the years in the 'year' column to datetime objects and store them in a new column 'datetime'
df_edit['datetime'] = [datetime.datetime(x, 1, 1) for x in df_edit.year]

# convert share percentage to float type
df_edit['share_percentage'] = df_edit['share_percentage'].astype('float64')

# save processed dataset to csv
processed_data_file = os.path.join(data_dir, dataset_name+'_edit.csv')
df_edit.to_csv(processed_data_file, index=False)

'''
Upload processed data to Carto
'''
logger.info('Uploading processed data to Carto.')
util_carto.upload_to_carto(processed_data_file, 'LINK')
'''
Upload original data and processed data to Amazon S3 storage
'''
# initialize AWS variables
aws_bucket = 'wri-public-data'
s3_prefix = 'resourcewatch/'

logger.info('Uploading original data to S3.')
# Copy the raw data into a zipped file to upload to S3
raw_data_dir = os.path.join(data_dir, dataset_name+'.zip')
with ZipFile(raw_data_dir,'w') as zipped:
    for file in raw_data_file:
        zipped.write(file, os.path.basename(file))
# Upload raw data file to S3
uploaded = util_cloud.aws_upload(raw_data_dir, aws_bucket, s3_prefix + os.path.basename(raw_data_dir))
logger.info('Uploading processed data to S3.')

# Copy the processed data into a zipped file to upload to S3
processed_data_dir = os.path.join(data_dir, dataset_name+'_edit.zip')
with ZipFile(processed_data_dir,'w') as zip:
    zip.write(processed_data_file, os.path.basename(processed_data_file)) 
        
# Upload processed data file to S3
uploaded = util_cloud.aws_upload(processed_data_dir, aws_bucket, s3_prefix + os.path.basename(processed_data_dir))

