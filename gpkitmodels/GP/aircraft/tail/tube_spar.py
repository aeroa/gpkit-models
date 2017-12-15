" tube spar "
from numpy import pi
from gpkitmodels.GP.materials import cfrpfabric
from gpkit import Model, parse_variables
from gpkitmodels import g

class TubeSpar(Model):
    """ Tail Boom Model

    Variables
    ---------
    mfac        1.0             [-]         weight margin factor
    k           0.8             [-]         taper index
    kfac        self.minusk2    [-]         (1-k/2)
    W                           [lbf]       spar weight

    Variables of length N-1
    -----------------------
    I                           [m^4]       moment of inertia
    d                           [in]        diameter
    t                           [in]        thickness
    dm                          [kg]        segment mass

    Upper Unbounded
    ---------------
    W

    Lower Unbounded
    ---------------
    J, l, I0

    LaTex Strings
    -------------
    kfac        (1-k/2)
    mfac        m_{\\mathrm{fac}}

    """

    minusk2 = lambda self, c: 1-c[self.k]/2.
    material = cfrpfabric

    def setup(self, N, surface):
        exec parse_variables(TubeSpar.__doc__)

        deta = surface.deta
        tmin = self.material.tmin
        rho = self.material.rho
        l = surface.l

        return [I <= pi*t*d**3/8.0,
                dm >= pi*rho*d*deta*t*kfac*l,
                W/mfac >= g*dm.sum(),
                t >= tmin]
