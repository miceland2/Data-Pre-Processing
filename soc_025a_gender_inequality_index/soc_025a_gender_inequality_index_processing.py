import pandas as pd
import io
import requests
import os
import sys
utils_path = os.path.join(os.path.abspath(os.getenv('PROCESSING_DIR')),'utils')
if utils_path not in sys.path:
    sys.path.append(utils_path)
import util_files
import util_cloud
import util_carto
import logging
from zipfile import ZipFile

# Set up logging
# Get the top-level logger object
logger = logging.getLogger()
for handler in logger.handlers: logger.removeHandler(handler)
logger.setLevel(logging.INFO)
# make it print to the console.
console = logging.StreamHandler()
logger.addHandler(console)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# name of table on Carto where you want to upload data
# this should be a table name that is not currently in use
dataset_name = 'soc_025a_gender_inequality_index' #check

logger.info('Executing script for dataset: ' + dataset_name)
# create a new sub-directory within your specified dir called 'data'
# within this directory, create files to store raw and processed data
data_dir = util_files.prep_dirs(dataset_name)

'''
Download data and save to your data directory
'''
# insert the url used to download the data from the source website
url = 'http://hdr.undp.org/sites/default/files/hdro_statistical_data_table_5.xlsx' #check

# read in data to pandas dataframe
r = requests.get(url)
df = pd.read_excel(io.BytesIO(r.content), encoding='utf8')

# save unprocessed source data to put on S3 (below)
raw_data_file = os.path.join(data_dir, os.path.basename(url))
df.to_excel(raw_data_file, header = False, index = False)

'''
Process data
'''

# drop header rows
df = df.iloc[7:] #check

# drop columns without data
df = df.drop(df.columns.difference(['Unnamed: 0','Table 5. Gender Inequality Index', 'Unnamed: 2','Unnamed: 4',
                                    'Unnamed: 6', 'Unnamed: 8','Unnamed: 10','Unnamed: 12', 'Unnamed: 14',
                                    'Unnamed: 16', 'Unnamed: 18']), 1) #check

#delete rows with missing values
df = df.dropna()

#rename columns
df.columns = ['HDI rank','Country','2018_GIIvalue', '2018_GIIrank', '2015 Maternal Mortality (per 1000 births)',
              '2015-2020 Adolescent birth rate (births per 1,000 women ages 15???19)',
              '2018 Share of seats in parliament','2010-2018 fem with secondary ed',
              '2010-2018 male with secondary ed', '2018 fem labor', '2018 male labor'] #check

#replace all '..' with None
df = df.replace({'..':None})
#replace all NaN with None
final_df=df.where((pd.notnull(df)), None)

#save processed dataset to csv
processed_data_file = os.path.join(data_dir, dataset_name+'_edit.csv')
final_df.to_csv(processed_data_file, index=False)

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
# Upload raw data file to S3

# Copy the raw data into a zipped file to upload to S3
raw_data_dir = os.path.join(data_dir, dataset_name+'.zip')
with ZipFile(raw_data_dir,'w') as zip:
    zip.write(raw_data_file, os.path.basename(raw_data_file))
# Upload raw data file to S3
uploaded = util_cloud.aws_upload(raw_data_dir, aws_bucket, s3_prefix+os.path.basename(raw_data_dir))

logger.info('Uploading processed data to S3.')
# Copy the processed data into a zipped file to upload to S3
processed_data_dir = os.path.join(data_dir, dataset_name+'_edit.zip')
with ZipFile(processed_data_dir,'w') as zip:
    zip.write(processed_data_file, os.path.basename(processed_data_file))
# Upload processed data file to S3
uploaded = util_cloud.aws_upload(processed_data_dir, aws_bucket, s3_prefix+os.path.basename(processed_data_dir))