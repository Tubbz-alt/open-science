from ruamel_yaml import YAML
import sys
sys.tracebacklimit = 0

# reading the configuration file
class ConfigReader(object):

    def __init__(self, yaml_file):

        with open(yaml_file, 'r') as stream:
            yaml = YAML()
            config = yaml.load(stream)

        # input parameters
        try:
            input_keywords = ["soc-point-file", "project-polygons", "grassland-mask"]
            self.input_files = self.validateParams(input_keywords, config['input-files'])
        except Exception:
            raise IOError('in YAML file one or more inputs variables not defined\n') from None

        # raster list
        try:
            raster_keywords = ["name", "band-list"]
            self.raster_list = []
            for raster in config['input-files']['raster-list']:
                raster_settings = self.validateParams(raster_keywords, config['input-files']['raster-list'][raster])
                self.raster_list.append(raster_settings)
        except Exception:
            raise IOError('in YAML file raster-list not defined') from None

        # bulk density
        try:
            model_keywords = ['method', 'pedotransfer-eq', 'constant']
            self.bd_params = self.validateParams(model_keywords, config['bulk-density'])
        except Exception:
            raise IOError('in YAML file one or more bulk density parameters not defined\n') from None

        # livestock data
        try:
            livestock_keywords = ['livestock-count', 'days-on-farm', 'EFliv']
            self.livestock_data = self.validateParams(livestock_keywords, config['livestock-data'])
        except Exception:
            raise IOError('in YAML file one or more livestock data not defined\n') from None

        # model parameters
        try:
            model_keywords = ['model-type', 'outlier-removal']
            self.model_params = self.validateParams(model_keywords, config['model-parameters'])
        except Exception:
            raise IOError('in YAML file one or more model parameters not defined\n') from None

    def validateParams(self, keywords, config):
        param_dict = {}
        for key in keywords:
            param_dict[key] = dict(config)[key]
        return param_dict
