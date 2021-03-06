import scipy as sp
import numpy as np
from scipy.stats import norm as dist


class Normal(object):

    n_params = 2
    problem_type = "regression"

    def __init__(self, params):
        self.loc = params[0]
        self.scale = np.exp(params[1])
        self.var = self.scale ** 2
        self.dist = dist(loc=self.loc, scale=self.scale)

    def __getattr__(self, name):
        if name in dir(self.dist):
            return getattr(self.dist, name)
        return None

    @property
    def params(self):
        return {'loc':self.loc, 'scale':self.scale}

    def __getitem__(self, key):
        return Normal(np.stack([self.loc[key], np.log(self.scale[key])]))

    def __len__(self):
        return len(self.loc)

    def fit(Y):
        m, s = sp.stats.norm.fit(Y)
        return np.array([m, np.log(s)])

    # log score methods
    def nll(self, Y):
        return -self.dist.logpdf(Y)

    def D_nll(self, Y):
        D = np.zeros((len(Y), 2))
        D[:, 0] = (self.loc - Y) / self.var
        D[:, 1] = 1 - ((self.loc - Y) ** 2) / self.var
        return D

    def fisher_info(self):
        FI = np.zeros((self.var.shape[0], 2, 2))
        FI[:, 0, 0] = 1 / self.var + 1e-5
        FI[:, 1, 1] = 2
        return FI

    # crps score methods
    def crps(self, Y):
        Z = (Y - self.loc) / self.scale
        return (self.scale * (Z * (2 * sp.stats.norm.cdf(Z) - 1) + \
                2 * sp.stats.norm.pdf(Z) - 1 / np.sqrt(np.pi)))

    def D_crps(self, Y):
        Z = (Y - self.loc) / self.scale
        D = np.zeros((len(Y), 2))
        D[:, 0] = -(2 * sp.stats.norm.cdf(Z) - 1)
        D[:, 1] = self.crps(Y) + (Y - self.loc) * D[:, 0]
        return D

    def crps_metric(self):
        I = np.c_[2 * np.ones_like(self.var), np.zeros_like(self.var),
                  np.zeros_like(self.var), self.var]
        I = I.reshape((self.var.shape[0], 2, 2))
        I = 1 / (2 * np.sqrt(np.pi)) * I
        return I

class NormalFixedVar(Normal):

    n_params = 1

    def __init__(self, params):
        self.loc = params[0]
        self.var = np.ones_like(self.loc)
        self.scale = np.ones_like(self.loc)
        self.shape = self.loc.shape
        self.dist = dist(loc=self.loc, scale=self.scale)

    def fit(Y):
        m, s = sp.stats.norm.fit(Y)
        return m

    # log score methods
    def D_nll(self, Y):
        D = np.zeros((len(Y), 1))
        D[:, 0] = (self.loc - Y) / self.var
        return D

    def fisher_info(self):
        FI = np.zeros((self.var.shape[0], 1, 1))
        FI[:, 0, 0] = 1 / self.var + 1e-5
        return FI

    # crps methods
    def D_crps(self, Y):
        Z = (Y - self.loc) / self.scale
        D = np.zeros((len(Y), 1))
        D[:, 0] = -(2 * sp.stats.norm.cdf(Z) - 1)
        return D

    def crps_metric(self): 
        I = np.c_[2 * np.ones_like(self.var)]
        I = I.reshape((self.var.shape[0], 1, 1))
        I = 1 / (2 * np.sqrt(np.pi)) * I
        return I
