" horizontal tail "
import numpy as np
from gpkit import Variable
from .tail_aero import TailAero
from gpkitmodels.GP.aircraft.wing.wing import Wing
from gpkitmodels.GP.aircraft.wing.wing_interior import WingInterior

#pylint: disable=attribute-defined-outside-init, unused-variable

class HorizontalTail(Wing):
    "horizontal tail model"
    flight_model = TailAero
    fillModel = WingInterior
    sparModel = None

    def setup(self, N=3, lam=0.8):
        self.ascs = Wing.setup(self, N)
        self.planform.substitutions.update({"AR": 4, "\\tau": 0.08,
                                            "\\lambda": 0.8})
        self.skin.substitutions.update({"\\rho_{CFRP}": 0.049})
        self.foam.substitutions.update({"\\bar{A}_{jh01}": 0.0548,
                                        "\\rho_{foam}": 0.024})
        Vh = Variable("V_h", "-", "horizontal tail volume coefficient")
        lh = Variable("l_h", "ft", "horizontal tail moment arm")
        CLhmin = Variable("(C_{L_h})_{min}", 0.75, "-",
                          "max downlift coefficient")
        mh = Variable("m_h", "-", "horizontal tail span effectiveness")

        return self.ascs, mh*(1+2.0/self.planform["AR"]) <= 2*np.pi

