" spar loading for gust case "
import os
from numpy import pi, hstack, cos
import pandas as pd
from gpkit import Variable, Vectorize
from gpfit.fit_constraintset import FitCS
from .sparloading import SparLoading

#pylint: disable=invalid-name, no-member, arguments-differ
#pylint: disable=attribute-defined-outside-init

class GustL(SparLoading):
    "spar loading model"
    new_qbarFun = None
    new_SbarFun = None

    def setup(self, static, Wcent, Wwing, V, CL):

        self.load = SparLoading.setup(self, static, Wcent)
        vgust = Variable("V_{gust}", 10, "m/s", "gust velocity")

        with Vectorize(static.N):
            agust = Variable("\\alpha_{gust}", "-", "gust angle of attack")
            return_cosm1 = lambda c: hstack(
                [1e-10, 1-cos(c[static["\\eta"]][1:]*pi/2)])
            cosminus1 = Variable("1-cos(\\eta)", return_cosm1,
                                 "-", "1 minus cosine factor")

        path = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(path + os.sep + "arctan_fit.csv").to_dict(
            orient="records")[0]

        constraints = [
            # fit for arctan from 0 to 1, RMS = 0.044
            FitCS(df, agust, [cosminus1*vgust/V]),
            self.beam["\\bar{q}"] >= self.static["\\bar{c}"]*(
                1 + 2*pi*agust/CL*(1+Wwing/Wcent)),
            ]

        return self.load, constraints
