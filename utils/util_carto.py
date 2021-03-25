import os
import time
import json
import requests
from carto.datasets import DatasetManager
from carto.auth import APIKeyAuthClient
from collections import OrderedDict
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def upload_to_carto(file, privacy, collision_strategy='skip'):
    '''
    Upload tables to Carto
    INPUT   file: location of file on local computer that you want to upload (string)
            privacy: the privacy setting of the dataset to upload to Carto (string)
            collision_strategy: determines what happens if a table with the same name already exists
            set the parameter to 'overwrite' if you want to overwrite the existing table on Carto
    '''
    # set up carto authentication using local variables for username (CARTO_WRI_RW_USER) and API key (CARTO_WRI_RW_KEY)
    auth_client = APIKeyAuthClient(api_key=os.getenv('CARTO_WRI_RW_KEY'), base_url="https://{user}.carto.com/".format(user=os.getenv('CARTO_WRI_RW_USER')))
    # set up dataset manager with authentication
    dataset_manager = DatasetManager(auth_client)
    # upload dataset to carto
    dataset = dataset_manager.create(file, collision_strategy = collision_strategy)
    logger.info('Carto table created: {}'.format(os.path.basename(file).split('.')[0]))
    # set dataset privacy
    dataset.privacy = privacy
    dataset.save()

def create_carto_schema(df):
    '''
    Function to create a dictionary of column names and data types
    in order to the upload the data to Carto
    INPUT   df: dataframe storing the data (dataframe)
    RETURN  ouput: an ordered dictionary (dictionary of strings)
    '''
    # create an empty list to store column names
    list_cols = []
    # get column names and types for data table
    # column types should be one of the following: geometry, text, numeric, timestamp
    for col in list(df):
        # if the column type is float64 or int64, assign the column type as numeric
        if (df[col].dtypes  == 'float')| (df[col].dtypes  == 'int'):
            list_cols.append((col, 'numeric'))
        # if the column type is geometry, assign the column type as geometry
        elif col  == 'geometry':
            list_cols.append(('the_geom', 'geometry'))
        # for all other columns assign them as text
        else:
            list_cols.append((col, 'text'))
    # create an ordered dictionary using the list
    output = OrderedDict(list_cols)

    return output

def sendSql(sql, user=None, key=None, f='', post=True):
    '''Send arbitrary sql and return response object or False'''
    url = "https://{user}.carto.com/".format(user)
    payload = {
        'api_key': key,
        'q': sql,
    }
    if len(f):
        payload['format'] = f
    logging.debug((url, payload))
    if post:
        r = requests.post(url, json=payload)
    else:
        r = requests.get(url, params=payload)
    r.raise_for_status()
    return r

def get(sql, user=None, key=None, f=''):
    '''Send arbitrary sql and return response object or False'''
    return sendSql(sql, user, key, f, False)

def getTables(user=None, key=None, f='csv'):
    '''Get the list of tables'''
    r = get('SELECT * FROM CDB_UserTables()', user, key, f)
    if f == 'csv':
        return r.text.splitlines()[1:]
    return r

def createTable(table, schema, user=None, key=None):
    '''
    Create table with schema and CartoDBfy table

    `schema` should be a dict or list of tuple pairs with
     - keys as field names and
     - values as field types
    '''
    items = schema.items() if isinstance(schema, dict) else schema
    defslist = ['{} {}'.format(k, v) for k, v in items]
    sql = 'CREATE TABLE "{}" ({})'.format(table, ','.join(defslist))
    if sendSql(sql, user, key):
        return _cdbfyTable(table, user, key)
    return False

def _cdbfyTable(table, user=None, key=None):
    '''CartoDBfy table so that it appears in Carto UI'''
    sql = "SELECT cdb_cartodbfytable('{}','\"{}\"')".format(user, table)
    return sendSql(sql, user, key)

def createIndex(table, fields, unique='', using='', user=None,
                key=None):
    '''Create index on table on field(s)'''
    fields = (fields,) if isinstance(fields, str) else fields
    f_underscore = '_'.join(fields)
    f_comma = ','.join(fields)
    unique = 'UNIQUE' if unique else ''
    using = 'USING {}'.format(using) if using else ''
    sql = 'CREATE {} INDEX idx_{}_{} ON {} {} ({})'.format(
        unique, table, f_underscore, table, using, f_comma)
    return sendSql(sql, user, key)


def checkCreateTable(table, schema, id_field='', time_field=''):
    '''
    Create the table if it does not exist, and pull list of IDs already in the table if it does
    INPUT   table: Carto table to check or create (string)
            schema: dictionary of column names and types, used if we are creating the table for the first time (dictionary)
            id_field: optional, name of column that we want to use as a unique ID for this table; this will be used to compare the
                    source data to the our table each time we run the script so that we only have to pull data we
                    haven't previously uploaded (string)
            time_field:  optional, name of column that will store datetime information (string)
    '''

    # check it the table already exists in Carto
    if table in getTables(user=os.getenv('CARTO_WRI_RW_USER'), key=os.getenv('CARTO_WRI_RW_KEY')):
        # if the table does exist, get a list of all the values in the id_field column
        print('Carto table already exists.')
    else:
        # if the table does not exist, create it with columns based on the schema input
        print('Table {} does not exist, creating'.format(table))
        createTable(table, schema, user=os.getenv('CARTO_WRI_RW_USER'), key=os.getenv('CARTO_WRI_RW_KEY'))
        # if a unique ID field is specified, set it as a unique index in the Carto table; when you upload data, Carto
        # will ensure no two rows have the same entry in this column and return an error if you try to upload a row with
        # a duplicate unique ID
        if id_field:
            createIndex(table, id_field, unique=True, user=os.getenv('CARTO_WRI_RW_USER'), key=os.getenv('CARTO_WRI_RW_KEY'))
        # if a time_field is specified, set it as an index in the Carto table; this is not a unique index
        if time_field:
            createIndex(table, time_field, user=os.getenv('CARTO_WRI_RW_USER'), key=os.getenv('CARTO_WRI_RW_KEY'))

def convert_geometry(geometries):
    '''
    Function to convert shapely geometries to geojsons
    INPUT   geometries: shapely geometries (list of shapely geometries)
    RETURN  output: geojsons (list of geojsons)
    '''
    output = []
    for geom in geometries:
        output.append(geom.__geo_interface__)
    return output

def _escapeValue(value, dtype):
    '''
    Escape value for SQL based on field type

    TYPE         Escaped
    None      -> NULL
    geometry  -> string as is; obj dumped as GeoJSON
    text      -> single quote escaped
    timestamp -> single quote escaped
    varchar   -> single quote escaped
    else      -> as is
    '''
    if value is None:
        return "NULL"
    if dtype == 'geometry':
        # if not string assume GeoJSON and assert WKID
        if isinstance(value, str):
            return value
        else:
            value = json.dumps(value)
            return "ST_SetSRID(ST_GeomFromGeoJSON('{}'),4326)".format(value)
    elif dtype in ('text', 'timestamp', 'varchar'):
        # quote strings, escape quotes, and drop nbsp
        return "'{}'".format(
            str(value).replace("'", "''"))
    else:
        return str(value)
    
def _dumpRows(rows, dtypes):
    '''Escapes rows of data to SQL strings'''
    dumpedRows = []
    for row in rows:
        escaped = [
            _escapeValue(row[i], dtypes[i])
            for i in range(len(dtypes))
        ]
        dumpedRows.append('({})'.format(','.join(escaped)))
    return ','.join(dumpedRows)

def insert_carto(row, table, schema, session):
    '''
    Function to upload data to the Carto table 
    INPUT   row: the geopandas dataframe of data we want to upload (geopandas dataframe)
            session: the request session initiated to send requests to Carto 
            schema: fields and corresponding data types of the Carto table
            table: name of the Carto table
    '''
    # replace all null values with None
    row = row.where(row.notnull(), None)
    # maximum attempts to make
    n_tries = 5
    # sleep time between each attempt   
    retry_wait_time = 6
    
    insert_exception = None
    # convert the geometry in the geometry column to geojsons
    row['geometry'] = convert_geometry(row['geometry'])
    # construct the sql query to upload the row to the carto table
    fields = schema.keys()
    values = _dumpRows([row.values.tolist()], tuple(schema.values()))
    sql = 'INSERT INTO "{}" ({}) VALUES {}'.format(table, ', '.join(fields), values)
    del values
    for i in range(n_tries):
        try:
            r = session.post('https://{}.carto.com/api/v2/sql'.format(os.getenv('CARTO_WRI_RW_USER')), json={'api_key': os.getenv('CARTO_WRI_RW_KEY'),'q': sql})
            r.raise_for_status()
        except Exception as e: # if there's an exception do this
            insert_exception = e
            logging.warning('Attempt #{} to upload row #{} unsuccessful. Trying again after {} seconds'.format(i, row['WDPA_PID'], retry_wait_time))
            logging.debug('Exception encountered during upload attempt: '+ str(e))
            time.sleep(retry_wait_time)
        else: # if no exception do this
            break # break this for loop, because we don't need to try again
    else:
        # this happens if the for loop completes, ie if it attempts to insert row n_tries times
        logging.error('Upload of row #{} has failed after {} attempts'.format(row['WDPA_PID'], n_tries))
        logging.error('Problematic row: '+ str(row))
        logging.error('Raising exception encountered during last upload attempt')
        logging.error(insert_exception)
        raise insert_exception
        
def shapefile_to_carto(table_name, schema, gdf, privacy):
    '''
    Function to upload a shapefile to Carto
    Note: Shapefiles can also be zipped and uploaded to Carto through the upload_to_carto function
          Use this function when several shapefiles are processed in one single script and need
          to be uploaded to separate Carto tables
          The function should also be used when the table is too large to be exported as a shapefile
    INPUT table_name: the name of the newly created table on Carto (string)
          schema: a dictionary of column names and data types in order to upload data to Carto (dictionary)
          gdf: a geodataframe storing all the data to upload (geodataframe)
          privacy: the privacy setting of the dataset to upload to Carto (string)
    '''
    # create a request session 
    s = requests.Session()
    # insert the rows contained in the geodataframe copy to the empty new table on Carto
    gdf.apply(insert_carto, args=(table_name, schema, s,), axis = 1)

    # Change privacy of table on Carto
    #set up carto authentication using local variables for username (CARTO_WRI_RW_USER) and API key (CARTO_WRI_RW_KEY)
    auth_client = APIKeyAuthClient(api_key=os.getenv('CARTO_WRI_RW_KEY'), base_url="https://{user}.carto.com/".format(user=os.getenv('CARTO_WRI_RW_USER')))
    #set up dataset manager with authentication
    dataset_manager = DatasetManager(auth_client)
    #set dataset privacy
    dataset = dataset_manager.get(table_name)
    dataset.privacy = privacy
    dataset.save()
