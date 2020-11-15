#!/usr/bin/env python3
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.optimize import differential_evolution
from scipy.interpolate import make_interp_spline, BSpline
from IPython import get_ipython
get_ipython().run_line_magic('matplotlib', 'inline')
plt.style.use('ggplot')


class LinearModel(object):

    def __init__(self, xVar, yVar, xData, yData):
        self.xVar = xVar
        self.yVar = yVar
        self.xData = xData
        self.yData = yData
        self.model = None
        self.model_results = None

    def  get_model_equation(self):
        pass

    def build_model(self, max_removal, type):
        self.generate_lm(max_removal, type)

    def outlier_influence(self):

        # model_influence
        influence = self.model_results.get_influence()
        n = self.xData.shape[0]

        # external studentized residuals (value > 3.0)
        studentized_residuals = np.array([abs(i) for i in influence.resid_studentized_external])
        studentized_score = np.where(studentized_residuals >= 3.0, 10, 0)

        # cooks distance (value > 1 || value > 4/n)
        cooks_distance = np.array(influence.cooks_distance[0])
        cooks_score = np.where((cooks_distance > 1) | (cooks_distance > 4 / n), 1, 0)

        # dfbetas
        dfbetas = np.array([abs(i[0]) for i in influence.dfbetas])
        dfbetas_score = np.where(dfbetas > 2 / np.sqrt(n), dfbetas, 0)
        dfbetas_score = np.where((dfbetas_score != 0) & (dfbetas_score == np.amax(dfbetas_score)), 1, 0)

        # dffits
        dffits = np.array([abs(i) for i in influence.dffits[0]])
        dffits_score = np.where(dffits > 2 / np.sqrt(n), dffits, 0)
        dffits_score = np.where((dffits_score != 0) & (dffits_score == np.amax(dffits_score)), 1, 0)

        # residual
        resid_score = np.where(studentized_residuals == np.amax(studentized_residuals), 1, 0)

        # fill df with scores
        influence_dict = {'studentized_ext': studentized_score,
                          'cooks': cooks_score,
                          'dfbetas': dfbetas_score,
                          'dffits': dffits_score,
                          'resid': resid_score
                          }

        outlier_scores = pd.DataFrame(influence_dict)
        outlier_scores["outlier_score"] = outlier_scores.sum(axis=1)

        if (outlier_scores["outlier_score"] > 1).any:
            return outlier_scores["outlier_score"].idxmax()
        else:
            return None

    def generate_lm(self, max_removal, type):
        """ Builds a linear model, recursively removing outliers to converge on
            a solution (highest r_squared).

            Parameters
            ----------
            max_removal : int
                Maximum number of outliers to remove from the dataset
        """
        # build linear model
        self.xData = sm.add_constant(self.xData)
        self.model = sm.OLS(self.yData, self.xData)
        self.model_results = self.model.fit()

        # remove outlier if exists and rebuild model
        if (max_removal > 0):
            outlier_loc = self.outlier_influence()
            if outlier_loc is not None:
                self.xData = self.xData.drop(outlier_loc)
                self.yData = self.yData.drop(outlier_loc)
                self.xData.index = range(len(self.xData))
                self.yData.index = range(len(self.yData))
                self.generate_lm(max_removal - 1, type)

        # drop constant column created by statsmodels
        if 'const' in self.xData:
            self.xData = self.xData.drop('const', axis=1)

    def plot_regression(self, output_file):

        # plot parameters
        df = self.xData.join(self.yData)
        x = df[self.xVar]
        m = self.model_results.params[self.xVar]
        b = self.model_results.params['const']
        # for legend
        if b >= 0:
            eq = 'y ={:7.3f}x +{:7.3f}'.format(m, b)
        else:
            eq = 'y ={:7.3f}x -{:7.3f}'.format(m, b)

        # build plot & save
        df.plot(kind='scatter', x=self.xVar, y='SOC', color='blue', alpha=0.5, figsize=(10, 6))
        plt.plot(x, m * x + b, color='darkblue', linewidth=1)
        plt.title('Sentinel-2 {} vs Soil Organic Carbon (%)'.format(self.xVar), size=22)
        plt.xlabel('Spectral Value (nm)'.format(self.xVar), size=18)
        plt.ylabel('Soil Organic Carbon (%)', size=18)
        plt.legend(labels=[eq, 'R_squared: {:4.3f}'.format(self.model_results.rsquared)], borderpad=0.8)
        plt.savefig(output_file)

    def save_model(self, output_file):
        """ Dumps model data and parameters to text file.

            Parameters
            ----------
            output_file : str
                path to text file
        """
        with open(output_file, 'w') as fh:
            fh.write(self.xData.join(self.yData).to_string())
            fh.write('\n')
            fh.write(self.model_results.summary().as_text())


# implemented using log transform in linear equation
class PowerModel(LinearModel):

    def __init__(self, xVar, yVar, xData, yData):
        super().__init__(xVar, yVar, xData, yData)

    def build_model(self, max_removal, type):
        self.xData = np.log(self.xData)
        self.yData = np.log(self.yData)
        self.generate_lm(max_removal, type)
        self.xData = np.exp(self.xData)
        self.yData = np.exp(self.yData)

    def plot_regression(self, output_file):

        # plot parameters
        df = self.xData.join(self.yData)
        x = df[self.xVar]
        a = np.exp(self.model_results.params['const'])
        b = self.model_results.params[self.xVar]
        eq = ("$y = {{{}}}x^{{{}}}$").format(round(a, 3), round(b, 3))  # for legend

        # splining technique to smooth plotted power regression line
        y_hat = a * np.power(x, b)
        y_hat = [y for _, y in sorted(zip(x, y_hat))]
        x_new = np.linspace(x.min(), x.max(), 800)
        spl = make_interp_spline(sorted(x), y_hat, k=3)  # type: BSpline
        power_smooth = spl(x_new)

        # build plot
        df.plot(kind='scatter', x=self.xVar, y='SOC', color='blue', alpha=0.5, figsize=(10, 6))
        plt.plot(x_new, power_smooth, color='darkblue', linewidth=1)
        plt.title('Sentinel-2 {} vs Soil Organic Carbon (%)'.format(self.xVar), size=22)
        plt.xlabel('Spectral Value (nm)'.format(self.xVar), size=18)
        plt.ylabel('Soil Organic Carbon (%)', size=18)
        plt.legend(labels=[eq, 'R_squared: {:4.3f}'.format(self.model_results.rsquared)], borderpad=0.8)
        plt.savefig(output_file)
