" cap spar "
from gpkit import Model, Variable, Vectorize
from sparloading import ChordSparL
from gustloading import GustL

class BoxSpar(Model):
    "cap spar model"
    def setup(self, N, surface):

        # phyiscal properties
        rhocfrp = Variable("\\rho_{CFRP}", 1.6, "g/cm^3", "density of CFRP")
        E = Variable("E", 2e7, "psi", "Youngs modulus of CFRP")

        with Vectorize(N-1):
            hin = Variable("h_{in}", "in", "inner spar height")
            I = Variable("I", "m^4", "spar x moment of inertia")
            Sy = Variable("S_y", "m**3", "section modulus")
            dm = Variable("dm", "kg", "segment spar mass")
            w = Variable("w", "in", "spar width")
            t = Variable("t", "in", "spar cap thickness")
            tshear = Variable("t_{shear}", "in", "shear web thickness")
            tcore = Variable("t_{core}", "in", "core thickness")

        W = Variable("W", "lbf", "spar weight")
        tcoret = Variable("(t_{core})/t", 0.02, "-", "core to thickness ratio")
        wlim = Variable("w_{lim}", 0.15, "-", "spar width to chord ratio")
        tshearmin = Variable("t_{shear-min}", 0.012, "in",
                             "min shear web thickness")
        g = Variable("g", 9.81, "m/s^2", "gravitational acceleration")
        mfac = Variable("m_{fac}", 0.97, "-", "curvature knockdown factor")
        rhofoam = Variable("\\rho_{foam}", 0.036, "g/cm^3", "foam density")

        constraints = [
            I/mfac <= w*t*hin**2,
            dm >= (rhocfrp*(4*w*t + 2*tshear*(hin + 2*tcore + 4*t))
                   + rhofoam*w*tcore*2)*surface["b"]/2*surface["d\\eta"],
            w <= wlim*surface["c_{ave}"],
            surface["c_{ave}"]*surface["\\tau"] >= hin + 4*t + 2*tcore,
            W >= 2*dm.sum()*g,
            Sy*(hin/2 + 2*t + tcore) <= I,
            tshear >= tshearmin,
            tcore >= tcoret*surface["c_{ave}"]*surface["\\tau"]
            ]

        self.loading = ChordSparL
        self.gustloading = GustL

        return constraints
