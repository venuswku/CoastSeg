import json
import datetime

from coastseg import exceptions
from coastseg import common

import geopandas as gpd
import numpy as np
from shapely import geometry
import pytest

def test_get_default_dict():
    # should return dict with fill dict values since keys exist in fill_dict
    default_str = "unknown"
    fill_dict = {'1':4,'2':5}
    keys = ['1','2']
    actual = common.get_default_dict(default=default_str,
                                     keys=keys,
                                     fill_dict=fill_dict)
    assert actual == fill_dict
    #should return dict with default values if no keys exist in fill_dict
    fill_dict = {'4':4,'5':5}
    expected = {'1':default_str,'2':default_str}
    actual = common.get_default_dict(default=default_str,
                                     keys=keys,
                                     fill_dict=fill_dict)
    assert actual == expected
    # should return dict with some default values if some keys exist in fill_dict
    fill_dict = {'1':4,'5':5}
    expected = {'1':4,'2':default_str}
    actual = common.get_default_dict(default=default_str,
                                     keys=keys,
                                     fill_dict=fill_dict)
    assert actual == expected

def test_is_list_empty():
    # empty list to test if it detects it as empty
    empty_list = [np.ndarray(shape=(0)),np.ndarray(shape=(0))]
    assert common.is_list_empty(empty_list) == True
    # half empty list to test if it detects it as not empty
    non_empty_list = [np.ndarray(shape=(1,2)),np.ndarray(shape=(0))]
    assert common.is_list_empty(non_empty_list) == False
    # full list to test if it detects it as not empty
    non_empty_list = [np.ndarray(shape=(2)),np.ndarray(shape=(2))]
    assert common.is_list_empty(non_empty_list) == False

def test_get_colors():
    length = 4
    actual_list = common.get_colors(length)
    assert len(actual_list) == length
    assert isinstance(actual_list,list)
    assert isinstance(actual_list[0],str)

def test_do_rois_filepaths_exist(tmp_path):
    # should return false when a filepath exist
    good_filepath = tmp_path
    roi_settings = {"1": {"filepath": str(good_filepath)}}
    return_value = common.do_rois_filepaths_exist(
        roi_settings, list(roi_settings.keys())
    )
    assert return_value == True
    # should return false when all filepaths exist
    good_filepath = tmp_path
    roi_settings = {
        "1": {"filepath": str(good_filepath)},
        "2": {"filepath": str(good_filepath)},
    }
    return_value = common.do_rois_filepaths_exist(
        roi_settings, list(roi_settings.keys())
    )
    assert return_value == True
    # should return false when a filepath doesn't exist
    bad_filepath = tmp_path / "fake"
    roi_settings = {"1": {"filepath": str(bad_filepath)}}
    return_value = common.do_rois_filepaths_exist(
        roi_settings, list(roi_settings.keys())
    )
    assert return_value == False
    # should return false when one filepath exist and one filepath doesn't exist
    roi_settings = {
        "1": {"filepath": str(good_filepath)},
        "2": {"filepath": str(bad_filepath)},
    }
    return_value = common.do_rois_filepaths_exist(
        roi_settings, list(roi_settings.keys())
    )
    assert return_value == False


def test_were_rois_downloaded_empty_roi_settings():
    actual_value = common.were_rois_downloaded(None, None)
    assert actual_value == False
    actual_value = common.were_rois_downloaded({}, None)
    assert actual_value == False


def test_do_rois_have_sitenames(valid_roi_settings, roi_settings_empty_sitenames):
    """Test if do_rois_have_sitenames returns true when
    each roi's 'sitename' != "" and false when each roi's 'sitename' == ""

    Args:
        valid_roi_settings (dict): roi_settings with ids["2","3","5"] and valid sitenames
        roi_settings_empty_sitenames(dict): roi_settings with ids["2"] and sitenames = ""
    """
    # ids of rois in valid_roi_settings
    roi_ids = ["2", "3", "5"]
    # when sitenames are not empty strings should return true
    actual_value = common.do_rois_have_sitenames(valid_roi_settings, roi_ids)
    assert actual_value == True

    roi_ids = ["2"]
    # when sitenames are not empty strings should return False
    actual_value = common.do_rois_have_sitenames(roi_settings_empty_sitenames, roi_ids)
    assert actual_value == False


def test_were_rois_downloaded(valid_roi_settings, roi_settings_empty_sitenames):
    """Test if were_rois_downloaded returns true when sitenames != "" and false sitenames == ""

    Args:
        valid_roi_settings (dict): roi_settings with ids["2","3","5"] and valid sitenames
        roi_settings_empty_sitenames(dict): roi_settings with ids["2"] and sitenames = ""
    """
    # ids of rois in valid_roi_settings
    roi_ids = ["2", "3", "5"]
    # when sitenames are not empty strings should return true
    actual_value = common.were_rois_downloaded(valid_roi_settings, roi_ids)
    assert actual_value == True

    roi_ids = ["2"]
    # when sitenames are not empty strings should return False
    actual_value = common.were_rois_downloaded(roi_settings_empty_sitenames, roi_ids)
    assert actual_value == False


def test_create_roi_settings(valid_selected_ROI_layer_data, valid_settings):
    """test if valid roi_settings dictionary is created when provided settings and a single selected ROI

    Args:
        valid_selected_ROI_layer_data (dict): geojson for ROI with id ="0"
        valid_settings (dict):
            download settings for ROI
            "sat_list": ["L5", "L7", "L8"],
            "landsat_collection": "C01",
            "dates": ["2018-12-01", "2019-03-01"],
    """
    filepath = "C\:Sharon"
    date_str = datetime.date(2019, 4, 13).strftime("%m-%d-%y__%I_%M_%S")
    actual_roi_settings = common.create_roi_settings(
        valid_settings, valid_selected_ROI_layer_data, filepath, date_str
    )
    expected_roi_id = valid_selected_ROI_layer_data["features"][0]["properties"]["id"]
    assert isinstance(actual_roi_settings, dict)
    assert expected_roi_id in actual_roi_settings
    assert set(actual_roi_settings[expected_roi_id]["dates"]) == set(
        valid_settings["dates"]
    )
    assert set(actual_roi_settings[expected_roi_id]["sat_list"]) == set(
        valid_settings["sat_list"]
    )
    assert (
        actual_roi_settings[expected_roi_id]["landsat_collection"]
        == valid_settings["landsat_collection"]
    )
    assert actual_roi_settings[expected_roi_id]["roi_id"] == expected_roi_id
    assert actual_roi_settings[expected_roi_id]["filepath"] == filepath


def test_config_dict_to_file(tmp_path):
    # test if file named config.json is saved when dictionary is passed
    config = {
        "0": {
            "dates": ["2018-12-01", "2019-03-01"],
            "sat_list": ["L8"],
            "roi_id": "0",
            "polygon": [
                [
                    [-124.19437983778509, 40.82355301978889],
                    [-124.19502680580241, 40.859579119105774],
                    [-124.14757559660633, 40.86006100475558],
                    [-124.14695430388457, 40.82403429740862],
                    [-124.19437983778509, 40.82355301978889],
                ]
            ],
            "landsat_collection": "C01",
            "sitename": "ID_0_datetime11-01-22__03_54_47",
            "filepath": "C:\\1_USGS\\CoastSeg\\repos\\2_CoastSeg\\CoastSeg_fork\\Seg2Map\\data",
        }
    }
    filepath = tmp_path
    common.config_to_file(config, filepath)
    assert tmp_path.exists()
    expected_path = tmp_path / "config.json"
    assert expected_path.exists()
    with open(expected_path, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)
    # test if roi id was saved as key and key fields exist
    assert "0" in data
    assert "dates" in data["0"]
    assert "sat_list" in data["0"]
    assert "roi_id" in data["0"]
    assert "polygon" in data["0"]
    assert "landsat_collection" in data["0"]
    assert "sitename" in data["0"]
    assert "filepath" in data["0"]


def test_config_geodataframe_to_file(tmp_path):
    # test if file named config_gdf.geojson is saved when geodataframe is passed
    d = {"col1": ["name1"], "geometry": [geometry.Point(1, 2)]}
    config = gpd.GeoDataFrame(d, crs="EPSG:4326")
    filepath = tmp_path
    common.config_to_file(config, filepath)
    assert tmp_path.exists()
    expected_path = tmp_path / "config_gdf.geojson"
    assert expected_path.exists()


def test_create_config_gdf(valid_rois_gdf, valid_shoreline_gdf, valid_transects_gdf):
    # test if a gdf is created with all the rois, shorelines and transects
    actual_gdf = common.create_config_gdf(
        valid_rois_gdf, valid_shoreline_gdf, valid_transects_gdf
    )
    assert "type" in actual_gdf.columns
    assert actual_gdf[actual_gdf["type"] == "transect"].empty == False
    assert actual_gdf[actual_gdf["type"] == "shoreline"].empty == False
    assert actual_gdf[actual_gdf["type"] == "roi"].empty == False

    # test if a gdf is created with all the rois, transects if shorelines is None
    shorelines_gdf = None
    actual_gdf = common.create_config_gdf(
        valid_rois_gdf, shorelines_gdf, valid_transects_gdf
    )
    assert "type" in actual_gdf.columns
    assert actual_gdf[actual_gdf["type"] == "transect"].empty == False
    assert actual_gdf[actual_gdf["type"] == "shoreline"].empty == True
    assert actual_gdf[actual_gdf["type"] == "roi"].empty == False
    # test if a gdf is created with all the rois if  transects and shorelines is None
    transects_gdf = None
    actual_gdf = common.create_config_gdf(valid_rois_gdf, shorelines_gdf, transects_gdf)
    assert "type" in actual_gdf.columns
    assert actual_gdf[actual_gdf["type"] == "transect"].empty == True
    assert actual_gdf[actual_gdf["type"] == "shoreline"].empty == True
    assert actual_gdf[actual_gdf["type"] == "roi"].empty == False


def test_convert_wgs_to_utm():
    # tests if valid espg code is returned by lon lat coordinates
    lon = 150
    lat = 100
    actual_espg = common.convert_wgs_to_utm(lon, lat)
    assert isinstance(actual_espg, str)
    assert actual_espg.startswith("326")
    lat = -20
    actual_espg = common.convert_wgs_to_utm(lon, lat)
    assert isinstance(actual_espg, str)
    assert actual_espg.startswith("327")


def test_get_center_rectangle():
    """test correct center of rectangle is returned"""
    expected_coords = [(4.0, 5.0), (4.0, 6.0), (8.0, 6.0), (8.0, 5.0), (4.0, 5.0)]
    center_x, center_y = common.get_center_rectangle(expected_coords)
    assert center_x == 6
    assert center_y == 5.5


def test_create_json_config(
    valid_settings,
    valid_roi_settings,
):
    # test if valid json style config is created when inputs dictionary contains multiple entries
    actual_config = common.create_json_config(valid_roi_settings, valid_settings)
    expected_roi_ids = list(valid_roi_settings.keys())

    assert isinstance(actual_config, dict)
    assert "settings" in actual_config.keys()
    assert "roi_ids" in actual_config.keys()
    assert isinstance(actual_config["roi_ids"], list)
    assert isinstance(actual_config["settings"], dict)
    assert actual_config["roi_ids"] == expected_roi_ids
    for key in expected_roi_ids:
        assert isinstance(actual_config[str(key)], dict)


def test_create_json_config_single_input(valid_settings, valid_single_roi_settings):
    # test if valid json style config is created when inputs dictionary contains only one entry
    actual_config = common.create_json_config(valid_single_roi_settings, valid_settings)
    expected_roi_ids = list(valid_single_roi_settings.keys())

    assert isinstance(actual_config, dict)
    assert "settings" in actual_config.keys()
    assert "roi_ids" in actual_config.keys()
    assert isinstance(actual_config["roi_ids"], list)
    assert isinstance(actual_config["settings"], dict)
    assert actual_config["roi_ids"] == expected_roi_ids
    for key in expected_roi_ids:
        assert isinstance(actual_config[str(key)], dict)


def test_extract_roi_by_id(valid_rois_gdf):
    # test if valid gdf is returned when id within gdf is given
    roi_id = 17
    actual_roi = common.extract_roi_by_id(valid_rois_gdf, roi_id)
    assert isinstance(actual_roi, gpd.GeoDataFrame)
    assert actual_roi[actual_roi["id"].astype(int) == roi_id].empty == False
    expected_roi = valid_rois_gdf[valid_rois_gdf["id"].astype(int) == roi_id]
    assert actual_roi["geometry"][0] == expected_roi["geometry"][0]
    assert actual_roi["id"][0] == expected_roi["id"][0]
