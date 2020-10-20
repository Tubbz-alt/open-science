#!/usr/bin/env python3
import os
import pandas as pd
from sklearn import linear_model
import config_reader as cfg
from sample_raster import SampleRasterValues

if __name__ == "__main__":

    # yaml
    config_file = os.path.dirname(os.path.realpath(__file__)) + os.sep + 'config.yml'

    # working directories
    data_dir = "/data"
    work_dir = "/work"
    output_dir = "/output"

    # read in input parameters
    input_params = cfg.ConfigReader(config_file)

    # extract raster values at sampling locations
    print('EXTRACING RASTER VALUES')
    svr = SampleRasterValues(input_params, data_dir)
    sampling_points = svr.sampleRasterValues()




import statsmodels.api as sm
import pandas as pd
import seaborn as sns
sns.set_context("paper")
import matplotlib.pyplot as plt
%matplotlib inline
plt.style.use('ggplot')


def generateLM(X, y):
    # build linear model
    X = sm.add_constant(X)
    model = sm.OLS(y, X)
    results = model.fit()

    # calculate external studentized residuals
    influence = results.get_influence()
    studentized_ext = [abs(x) for x in influence.resid_studentized_external]

    # remove outlier if exists and rebuild model
    for resid in studentized_ext:
        if resid > 3.0:
            outlier_loc = studentized_ext.index(resid)
            x_new = X.drop(outlier_loc)
            y_new = y.drop(outlier_loc)
            X, y, results, model = generateLM(x_new, y_new)

    # drop constant column created by statsmodels
    if 'const' in X:
        X = X.drop('const', axis=1)

    return X, y, results, model
    

def plot_regression(df, results, x_name, output_file):
    # coefficients from linear regression model
    m = results.params[x_name]
    b = results.params['const']

    df.plot(kind='scatter', x=x_name, y='SOC', color='blue', alpha=0.5, figsize=(10,6))
    plt.plot(df[x_name], m*df[x_name] + b, color='darkblue', linewidth=1)
    plt.title('Sentinel-2 {} vs Soil Organic Carbon (%)'.format(x_name), size=22)
    plt.xlabel('Spectral Value (nm)'.format('B12'), size=18)
    plt.ylabel('Soil Organic Carbon (%)', size=18)
    plt.legend(labels=['y ={:7.3f}x +{:7.3f}'.format(m, x), 'R_squared: {:4.3f}'.format(results.rsquared)], borderpad=0.8)
    plt.savefig(output_file)



sample_values = r'C:\Users\sambe\Documents\regen\open-science\soc\scripts\output\soc_spectral_values_avg.csv'
df = pd.read_csv(sample_values)
df = df.drop(columns=['Unnamed: 0'], axis=1)

df

X = df['B12']
y = df['SOC']

x_new, y_new, results, model = generateLM(X, y)
df_new = x_new.join(y_new)
