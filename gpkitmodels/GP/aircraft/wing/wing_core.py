" wing interior "
from gpkit import Model, parse_variables

#pylint: disable=exec-used, no-member, undefined-variable

class WingCore(Model):
    """ Wing Core Model

    Variables
    ---------
    W                           [lbf]       wing core weight
    rhocore         0.036       [g/cm^3]    core density
    Abar            0.0753449   [-]         normalized cross section area
    g               9.81        [m/s^2]     graviataional constant

    Upper Unbounded
    ---------------
    W

    Lower Unbounded
    ---------------
    cave, b

    LaTex Strings
    -------------
    rhocore                 \\rho_{\\mathrm{core}}
    Abar                    \\bar{A}

    """
    def setup(self, surface):
        exec parse_variables(WingCore.__doc__)

        cave = self.cave = surface.cave
        b = self.b = surface.b
        deta = surface.deta

        return [W >= 2*(g*rhocore*Abar*cave**2*b/2*deta).sum()]
