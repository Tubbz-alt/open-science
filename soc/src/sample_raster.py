########################################################
# Name: Sample Raster Values
# Source Name: sample_raster.py
# Author: Sam Bennetts
# Usage: Extracts spectral values from points on raster
# Date: 8.31.2020
# Modified: 9.5.2020
########################################################

# Python modules
import os
import pandas as pd

# Geospatial modules
import geopandas as gpd
import rasterio as rio
import rasterstats as rstats


class SampleRasterValues(object):

    def __init__(self, config, data_dir):

        self.input_dir = data_dir
        self.sample_locations = os.path.join(self.input_dir, config.input_files['soc-point-file'])
        self.raster_list = config.raster_list
        self.output_dir = "/output"

        # validate input rasters and point file
        if not os.path.exists(self.sample_locations):
            print(self.sample_locations)
            raise IOError("in SOC sampling point file does not exist", self.sample_locations)

        for raster in self.raster_list:
            if not os.path.exists(os.path.join(self.input_dir, raster['name'])):
                raise IOError("in SRV raster does not exist", raster)

    def getRasterMeta(self, input_raster):
        with rio.open(input_raster) as src:
            return src.meta

    def extractRasterValue(self, point, raster, band):
        return rstats.point_query(point, raster, band, interpolate='nearest')[0]

    def sampleRasterValues(self):
        # read in sampling point file
        sampling_points = gpd.read_file(self.sample_locations)
        sampling_points['key'] = sampling_points.index

        for raster in self.raster_list:
            # get raster metadata
            input_raster = os.path.join(self.input_dir, raster['name'])
            raster_meta = self.getRasterMeta(input_raster)
            band_count = raster_meta['count']
            band_names = raster['band-list']

            # reproject sampling points
            points_df = sampling_points
            if not raster_meta['crs'] == points_df.crs:
                points_df = points_df.to_crs(raster_meta['crs'])

            # extract spectral values
            spectral_values = []
            for index, row in points_df.iterrows():
                r_vals = [self.extractRasterValue(row.geometry, input_raster, i+1) for i in range(band_count)]
                spectral_values.append([row.key] + r_vals)

            # merge datasets
            cols = ['key'] + band_names
            svals_df = pd.DataFrame(spectral_values, columns=cols)
            sampling_points = sampling_points.merge(svals_df, on='key')

        # write smoothed data to csv
        output_file = os.path.join(self.output_dir, "soc_spectral_values_avg.csv")
        sampling_points = sampling_points.drop(columns=['geometry', 'key'], axis=1)
        sampling_points_avg = sampling_points.groupby('Name', as_index=False).mean()
        sampling_points_avg.to_csv(output_file)

        return sampling_points_avg
