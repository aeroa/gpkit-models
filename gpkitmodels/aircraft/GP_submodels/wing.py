" wing.py "
import numpy as np
from gpkit import Variable, Model, vectorize
from wing_interior import WingInterior
from wing_skin import WingSkin
from capspar import CapSpar
from constant_taper_chord import c_bar

class Wing(Model):
    "The thing that creates the lift"
    def __init__(self, N=5, lam=0.5, **kwargs):

        W = Variable("W", "lbf", "weight")
        mfac = Variable("m_{fac}", 1.2, "-", "wing weight margin factor")
        S = Variable("S", "ft^2", "surface area")
        A = Variable("A", "-", "aspect ratio")
        b = Variable("b", "ft", "wing span")
        tau = Variable("\\tau", 0.115, "-", "airfoil thickness ratio")
        CLmax = Variable("C_{L_{max}}", 1.39, "-", "maximum CL of JHO1")
        CM = Variable("C_M", 0.14, "-", "wing moment coefficient")
        mw = Variable("m_w", 2.0*np.pi/(1+2.0/23), "-",
                      "assumed span wise effectiveness")
        croot = Variable("c_{root}", "ft", "root chord")
        cmac = Variable("c_{MAC}", "ft", "mean aerodynamic chord")
        cb = c_bar(lam, N)
        with vectorize(N):
            cbar = Variable("\\bar{c}", cb, "-",
                            "normalized chord at mid element")
        with vectorize(N-1):
            cave = Variable("c_{ave}", "ft", "mid section chord")

        self.flight_model = WingAero

        constraints = [b**2 == S*A,
                       tau == tau,
                       CLmax == CLmax,
                       CM == CM,
                       mw == mw,
                       cbar == cbar,
                       cave == (cb[1:] + cb[:-1])/2*S/b,
                       croot == S/b*cb[0],
                       cmac == S/b]

        self.capspar = CapSpar(b, cave, tau, N)
        self.wingskin = WingSkin(S, croot, b)
        self.winginterior = WingInterior(cave, b, N)
        self.components = [self.capspar, self.wingskin, self.winginterior]
        self.loading = WingLoading

        constraints.extend([W/mfac >= sum(c["W"] for c in self.components)])

        Model.__init__(self, None, [self.components, constraints],
                       **kwargs)

class WingLoading(Model):
    "wing loading cases"
    def __init__(self, wing, Wcent, **kwargs):

        skinloading = wing.wingskin.loading(wing.wingskin)
        caploading = wing.capspar.loading(wing.capspar, Wcent)

        Model.__init__(self, None, [skinloading, caploading], **kwargs)

class WingAero(Model):
    "wing aerodynamic model with profile and induced drag"
    def __init__(self, static, state, **kwargs):
        "wing drag model"
        Cd = Variable("C_d", "-", "wing drag coefficient")
        CL = Variable("C_L", "-", "lift coefficient")
        e = Variable("e", 0.9, "-", "Oswald efficiency")
        Re = Variable("Re", "-", "Reynold's number")
        cdp = Variable("c_{dp}", "-", "wing profile drag coeff")

        constraints = [
            Cd >= cdp + CL**2/np.pi/static["A"]/e,
            cdp**3.72 >= (0.0247*CL**2.49*Re**-1.11
                          + 2.03e-7*CL**12.7*Re**-0.338
                          + 6.35e10*CL**-0.243*Re**-3.43
                          + 6.49e-6*CL**-1.9*Re**-0.681),
            Re == state["\\rho"]*state["V"]*static["c_{MAC}"]/state["\\mu"],
            ]

        Model.__init__(self, None, constraints, **kwargs)

