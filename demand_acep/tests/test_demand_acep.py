"""
This is the place for all the unit tests for the package demand_acep.
We can refactor this if this becomes too large.

"""
# %% Imports

import os
import sys
import numpy as np
import pandas as pd
import pdb

from itertools import groupby
from operator import itemgetter

# To import files from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from demand_acep import extract_data
from demand_acep import extract_ppty
from demand_acep import data_resample
from demand_acep import data_impute
from demand_acep import compute_interpolation
from demand_acep import build_interpolation
from demand_acep import long_missing_data_prep
# %% Paths
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# dirpath = os.path.join(path, 'data/measurements/2018/07/01')
# filename = 'PokerFlatResearchRange-PokerFlat-PkFltM1AntEaDel@2018-07-02T081007Z@PT23H@PT146F.nc'
dirpath = os.path.join(path, 'data/measurements/2019/01/03')
filename = 'PokerFlatResearchRange-PokerFlat-PkFltM3SciEaDel@2019-01-03T093004Z@P1D@PT179F.nc'


def test_extract_data():
    test_df = extract_data(dirpath, filename)
    column_name = test_df.columns.tolist()[0]

    assert (test_df.index.dtype == 'datetime64[ns]'), "The first output from this function should be a timedelta object"

    assert (test_df[column_name].dtype == 'float64'), "The second output from this function should be numpy array"

    return


def test_extract_ppty():
    meter_name = ['PkFltM1Ant', 'PkFltM2Tel', 'PkFltM3Sci', 'PQube3']
    [test_meter, test_channel] = extract_ppty(filename, meter_name)

    assert (any(val == test_meter for val in meter_name)), "Returned meter name does not exist"

    assert (test_channel in filename), "Returned measurement channel does not exist"

    return


def test_data_resample():
    test_df = extract_data(dirpath, filename)
    test_resampled = data_resample(test_df, sample_time='1T')
    diff_test = np.diff(test_resampled.index)
    time_1T_ns = np.timedelta64(60000000000,'ns') # sample_time 1T in nanoseconds
    assert (np.all(np.equal(diff_test, time_1T_ns))), "Data not properly downsamples"

    return


def test_data_impute():
    test_df = extract_data(dirpath, filename)
    test_df = data_impute(test_df)
    dict_assert = []
    if isinstance(test_df, dict):
        for meter in test_df:
            dict_assert.append(test_df[meter].notnull().values.all())
        assert (all(val for val in dict_assert)), "Data imputations in dictionary not functioning properly as data " \
                                                  "still contains NaN"
    else:
        assert (test_df.notnull().values.all()), "Data imputations in Dataframes not functioning properly as data " \
                                                 "still contains NaN"

    return


def test_build_interpolation():
    df = extract_data(dirpath, filename)
    test_resampled = data_resample(df, sample_time='1T')
    test_df = test_resampled.copy()
    # gets the index location in integers where the NaNs are located
    get_nan_idx = np.where(test_df.isna())[0]
    idx_grp_nan = []
    # creates a list of consecutive index locations to determine the range of interpolation
    for k, g in groupby(enumerate(get_nan_idx), lambda ix: ix[0] - ix[1]):
        idx_grp_nan.append(list(map(itemgetter(1), g)))
    # performs interpolation for each consecutive NaN index location
    for idx, val in enumerate(idx_grp_nan):
        n_grp = len(val)
        # for each range of consecutive NaN locations, use data points of length equal to the number that NaNs in that
        # range before and after the NaN datapoints
        prev_idx = val[0] - n_grp
        next_idx = val[-1] + n_grp
        # This if-else clause handles edge cases
        # If - When the number of consecutive NaN points is larger than the number of available data points before it in
        # the dataframe.
        # Elif - When the number of consecutive NaN points is larger than the number of available data points after it
        # in the dataframe.
        if prev_idx < 0:
            prev_vals = test_df.iloc[0:val[0]]
            next_vals = test_df.iloc[val[0] + 1: next_idx + 1]
        elif next_idx > len(test_df):
            prev_vals = test_df.iloc[prev_idx:val[0]]
            next_vals = test_df.iloc[val[0] + 1: len(test_df)]
        else:
            prev_vals = test_df.iloc[prev_idx:val[0]]
            next_vals = test_df.iloc[val[0] + 1: next_idx + 1]
        y_values = prev_vals.append(next_vals)
    y_interp = build_interpolation(y_values, n_grp)
    # pdb.set_trace()
    # check that y_interp is has no NaN values
    assert (~np.isnan(y_interp).any()), "Interpolation function not fully replacing NaN with interpolation values"
    # check that y_interp is within reasonable range from y_values
    max_val = np.max(y_values) + np.std(y_values)
    min_val = np.min(y_values) - np.std(y_values)
    assert (y_interp.all() < max_val).all() or (y_interp.all() > min_val).all(), "Error in determining a function fit " \
                                                                                 "through interpolation"

    assert (y_interp.dtype == 'float64'), "The output from this function should be numpy array"
    return


def test_compute_interpolation():
    test_df = extract_data(dirpath, filename)
    if isinstance(test_df, dict):
        for meter in test_df:
            assert (isinstance(test_df[meter], pd.DataFrame)), "Object passed in is not a Dataframe"
            if test_df[meter].isnull().values.any():
                test_df[meter] = test_df[meter].apply(compute_interpolation)
                assert (test_df[meter].notnull().values.all()), "Data imputations in Series not functioning properly " \
                                                                "as data still contains NaN"
    else:
        assert (isinstance(test_df, pd.DataFrame)), "Object passed in is not a Dataframe"
        if test_df.isnull().values.any():
            test_df = test_df.apply(compute_interpolation)
            assert (test_df.notnull().values.all()), "Data imputations in Series not functioning properly as data " \
                                                     "still contains NaN"

    return


def test_long_missing_data_prep():
    dirpath_data = os.path.join(path, 'data/measurements/test_data')
    filename_data = 'PQube3_comb.csv'

    meter_mod_df = long_missing_data_prep(dirpath_data, filename_data)

    assert (filename_data[-4:] == '.csv'), "File passed in is not in a .csv format"
    assert (isinstance(meter_mod_df, pd.DataFrame)), "Object returned in is not a Dataframe"
    meter_df = pd.read_csv(os.path.join(dirpath_data, filename_data))
    assert (len(meter_mod_df) >= len(meter_df)), "Returned DataFrame should be greater than or equal to the data " \
                                                 "passed in"
    diff_test = np.diff(meter_mod_df.index)
    time_1T_ns = np.timedelta64(60000000000, 'ns')  # sample_time 1T in nanoseconds
    assert (np.all(np.equal(diff_test, time_1T_ns))), "DateTimeIndex intervals not properly computed in function"

    return




