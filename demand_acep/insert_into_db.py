# This file handles the databse insertion

from sqlalchemy import * 
import pandas as pd

# %% Imports
import os
import pandas as pd
import pdb

from demand_acep import extract_data
from demand_acep import extract_ppty


def insert_into_database(sql_engine, data_date, data_root_path):
    """ 
    This function inserts into the database for the data_date specified
    
    Parameters
    ----------
    sql_engine : SQLAlchemy databse engine
        `sql_engine` should support database operation.
    data_date : string
        `data_date` string will be used to extract the year and the path to the
        data.
    data_root_path: string
        `data_root_path` should contain the root path of the data where the 
        further directory structure for dates like year\month\day is located.

    Returns
    -------
    int
        Description of anonymous integer return value.
    """
    
    # Look for the pickle and file and use pandas_to_sql to insert the data 
    # into the database. 
    
    
    return 