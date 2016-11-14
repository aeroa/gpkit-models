"""Jungle Hawk Owl"""
import numpy as np
from submodels.breguet_endurance import BreguetEndurance
from submodels.flight_state import FlightState
from submodels.gas_engine import Engine
from gpkit import Model, Variable, vectorize, units

# pylint: disable=invalid-name

class Aircraft(Model):
    "the JHO vehicle"
    def __init__(self, Wfueltot, DF70=False, **kwargs):
        self.flight_model = AircraftPerf
        self.fuselage = Fuselage(Wfueltot)
        self.wing = Wing()
        self.engine = Engine(DF70)
        self.empennage = Empennage()

        components = [self.fuselage, self.wing, self.engine, self.empennage]
        self.smeared_loads = [self.fuselage, self.engine]

        self.loading = AircraftLoading

        Wzfw = Variable("W_{zfw}", "lbf", "zero fuel weight")
        Wpay = Variable("W_{pay}", 10, "lbf", "payload weight")
        Wavn = Variable("W_{avn}", 8, "lbf", "avionics weight")

        constraints = [
            Wzfw >= sum(summing_vars(components, "W")) + Wpay + Wavn,
            self.empennage.horizontaltail["V_h"] <= (
                self.empennage.horizontaltail["S"]
                * self.empennage.horizontaltail["l_h"]/self.wing["S"]**2
                * self.wing["b"]),
            self.empennage.verticaltail["V_v"] <= (
                self.empennage.verticaltail["S"]
                * self.empennage.verticaltail["l_v"]/self.wing["S"]
                / self.wing["b"]),
            self.wing["C_{L_{max}}"]/self.wing["m_w"] <= (
                self.empennage.horizontaltail["C_{L_{max}}"]
                / self.empennage.horizontaltail["m_h"])
            ]

        Model.__init__(self, None, [components, constraints],
                       **kwargs)

def summing_vars(models, varname):
    "returns a list of variables with shared varname in model list"
    modelnames = [m.__class__.__name__ for m in models]
    vkeys = np.hstack([list(m.varkeys[varname]) for m in models])
    vkeys = [v for v in vkeys if v.models[-1] in modelnames]
    vrs = [m[v] for m, v in zip(models, vkeys)]
    return vrs

class AircraftLoading(Model):
    "aircraft loading model"
    def __init__(self, aircraft, Wcent, **kwargs):

        loading = [aircraft.wing.loading(aircraft.wing, Wcent)]
        loading.append(aircraft.empennage.loading(aircraft.empennage))
        loading.append(aircraft.fuselage.loading(aircraft.fuselage, Wcent))

        tbstate = TailBoomState()
        loading.append(TailBoomFlexibility(aircraft.empennage.horizontaltail,
                                           aircraft.empennage.tailboom,
                                           aircraft.wing, tbstate, **kwargs))

        Model.__init__(self, None, loading, **kwargs)

class AircraftPerf(Model):
    "performance model for aircraft"
    def __init__(self, static, state, **kwargs):

        self.wing = static.wing.flight_model(static.wing, state)
        self.fuselage = static.fuselage.flight_model(static.fuselage, state)
        self.engine = static.engine.flight_model(static.engine, state)
        self.htail = static.empennage.horizontaltail.flight_model(
            static.empennage.horizontaltail, state)
        self.vtail = static.empennage.verticaltail.flight_model(
            static.empennage.verticaltail, state)
        self.tailboom = static.empennage.tailboom.flight_model(
            static.empennage.tailboom, state)

        self.dynamicmodels = [self.wing, self.fuselage, self.engine,
                              self.htail, self.vtail, self.tailboom]
        areadragmodel = [self.fuselage, self.htail, self.vtail, self.tailboom]
        areadragcomps = [static.fuselage, static.empennage.horizontaltail,
                         static.empennage.verticaltail,
                         static.empennage.tailboom]

        Wend = Variable("W_{end}", "lbf", "vector-end weight")
        Wstart = Variable("W_{start}", "lbf", "vector-begin weight")
        CD = Variable("C_D", "-", "drag coefficient")
        CDA = Variable("CDA", "-", "area drag coefficient")
        mfac = Variable("m_{fac}", 1.7, "-", "drag margin factor")

        dvars = []
        for dc, dm in zip(areadragcomps, areadragmodel):
            if "C_f" in dm.varkeys:
                dvars.append(dm["C_f"]*dc["S"]/static.wing["S"])

        constraints = [Wend == Wend,
                       Wstart == Wstart,
                       CDA/mfac >= sum(dvars),
                       CD >= CDA + self.wing["C_d"]]

        Model.__init__(self, None, [self.dynamicmodels, constraints], **kwargs)

class FlightSegment(Model):
    "creates flight segment for aircraft"
    def __init__(self, N, aircraft, alt=15000, onStation=False, wind=False,
                 etap=0.7, **kwargs):

        self.aircraft = aircraft

        with vectorize(N):
            self.fs = FlightState(alt, onStation, wind)
            self.aircraftPerf = self.aircraft.flight_model(self.aircraft,
                                                           self.fs)
            self.slf = SteadyLevelFlight(self.fs, self.aircraft,
                                         self.aircraftPerf, etap)
            self.be = BreguetEndurance(self.aircraftPerf)

        self.submodels = [self.fs, self.aircraftPerf, self.slf, self.be]

        Wfuelfs = Variable("W_{fuel-fs}", "lbf", "flight segment fuel weight")

        self.constraints = [Wfuelfs >= self.be["W_{fuel}"].sum()]

        if N > 1:
            self.constraints.extend([self.aircraftPerf["W_{end}"][:-1] >=
                                     self.aircraftPerf["W_{start}"][1:]])

        Model.__init__(self, None, [self.aircraft, self.submodels,
                                    self.constraints], **kwargs)

class Loiter(Model):
    "make a loiter flight segment"
    def __init__(self, N, aircraft, alt=15000, onStation=False, wind=False,
                 etap=0.7, **kwargs):
        fs = FlightSegment(N, aircraft, alt, onStation, wind, etap)

        t = Variable("t", 6, "days", "time loitering")
        constraints = [fs.be["t"] >= t/N]

        Model.__init__(self, None, [constraints, fs], **kwargs)

class Cruise(Model):
    "make a cruise flight segment"
    def __init__(self, N, aircraft, alt=15000, onStation=False, wind=False,
                 etap=0.7, R=200, **kwargs):
        fs = FlightSegment(N, aircraft, alt, onStation, wind, etap)

        R = Variable("R", R, "nautical_miles", "Range to station")
        constraints = [R/N <= fs["V"]*fs.be["t"]]

        Model.__init__(self, None, [fs, constraints], **kwargs)

class Climb(Model):
    "make a climb flight segment"
    def __init__(self, N, aircraft, alt=15000, onStation=False, wind=False,
                 etap=0.7, dh=15000, **kwargs):
        fs = FlightSegment(N, aircraft, alt, onStation, wind, etap)

        with vectorize(N):
            hdot = Variable("\\dot{h}", "ft/min", "Climb rate")

        deltah = Variable("\\Delta_h", dh, "ft", "altitude difference")
        hdotmin = Variable("\\dot{h}_{min}", 100, "ft/min",
                           "minimum climb rate")

        constraints = [
            hdot*fs.be["t"] >= deltah/N,
            hdot >= hdotmin,
            fs.slf["T"] >= (0.5*fs["\\rho"]*fs["V"]**2*fs["C_D"]
                            * fs.aircraft.wing["S"] + fs["W_{start}"]*hdot
                            / fs["V"]),
            ]

        Model.__init__(self, None, [fs, constraints], **kwargs)

class SteadyLevelFlight(Model):
    "steady level flight model"
    def __init__(self, state, aircraft, perf, etap, **kwargs):

        T = Variable("T", "N", "thrust")
        etaprop = Variable("\\eta_{prop}", etap, "-", "propulsive efficiency")

        constraints = [
            (perf["W_{end}"]*perf["W_{start}"])**0.5 <= (
                0.5*state["\\rho"]*state["V"]**2*perf["C_L"]
                * aircraft.wing["S"]),
            T >= (0.5*state["\\rho"]*state["V"]**2*perf["C_D"]
                  *aircraft.wing["S"]),
            perf["P_{shaft}"] >= T*state["V"]/etaprop]

        Model.__init__(self, None, constraints, **kwargs)

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

def c_bar(lam, N):
    "returns wing chord lengths for constant taper wing"
    eta = np.linspace(0, 1, N)
    c = 2/(1+lam)*(1+(lam-1)*eta)
    return c

class WingLoading(Model):
    "wing loading cases"
    def __init__(self, wing, Wcent, **kwargs):

        skinloading = wing.wingskin.loading(wing.wingskin)
        caploading = wing.capspar.loading(wing.capspar, Wcent)

        Model.__init__(self, None, [skinloading, caploading], **kwargs)

class WingInterior(Model):
    "wing interior model"
    def __init__(self, cave, b, N, **kwargs):

        W = Variable("W", "lbf", "interior mass of wing")
        rhofoam = Variable("\\rho_{foam}", 0.036, "g/cm^3", "foam density")
        Abar = Variable("\\bar{A}_{jh01}", 0.0753449, "-",
                        "jh01 non dimensional area")
        g = Variable("g", 9.81, "m/s^2", "gravitational acceleration")

        constraints = [W >= 2*(g*rhofoam*Abar*cave**2*(b/2)/(N-1)).sum()]

        Model.__init__(self, None, constraints, **kwargs)

class WingSkin(Model):
    "wing skin model"
    def __init__(self, S, croot, b, **kwargs):

        rhocfrp = Variable("\\rho_{CFRP}", 1.4, "g/cm^3", "density of CFRP")
        W = Variable("W", "lbf", "wing skin weight")
        g = Variable("g", 9.81, "m/s^2", "gravitational acceleration")
        t = Variable("t", "in", "wing skin thickness")
        tmin = Variable("t_{min}", 0.012, "in",
                        "minimum gague wing skin thickness")
        Jtbar = Variable("\\bar{J/t}", 0.01114, "1/mm",
                         "torsional moment of inertia")

        self.loading = WingSkinL

        constraints = [W >= rhocfrp*S*2*t*g,
                       t >= tmin,
                       Jtbar == Jtbar,
                       b == b,
                       croot == croot]

        Model.__init__(self, None, constraints, **kwargs)

class WingSkinL(Model):
    "wing skin loading model for torsional loads in skin"
    def __init__(self, static, **kwargs):

        taucfrp = Variable("\\tau_{CFRP}", 570, "MPa", "torsional stress limit")
        Cmw = Variable("C_{m_w}", 0.121, "-", "negative wing moment coefficent")
        rhosl = Variable("\\rho_{sl}", 1.225, "kg/m^3",
                         "air density at sea level")
        Vne = Variable("V_{NE}", 45, "m/s", "never exceed vehicle speed")

        constraints = [
            taucfrp >= (1/static["\\bar{J/t}"]/(static["c_{root}"])**2
                        / static["t"]*Cmw*static["S"]*rhosl*Vne**2)]

        Model.__init__(self, None, constraints, **kwargs)

class CapSpar(Model):
    "cap spar model"
    def __init__(self, b, cave, tau, N=5, **kwargs):
        self.N = N

        # phyiscal properties
        rhocfrp = Variable("\\rho_{CFRP}", 1.4, "g/cm^3", "density of CFRP")
        E = Variable("E", 2e7, "psi", "Youngs modulus of CFRP")

        with vectorize(self.N-1):
            t = Variable("t", "in", "spar cap thickness")
            hin = Variable("h_{in}", "in", "inner spar height")
            w = Variable("w", "in", "spar width")
            I = Variable("I", "m^4", "spar x moment of inertia")
            dm = Variable("dm", "kg", "segment spar mass")

        W = Variable("W", "lbf", "spar weight")
        w_lim = Variable("w_{lim}", 0.15, "-", "spar width to chord ratio")
        g = Variable("g", 9.81, "m/s^2", "gravitational acceleration")

        self.loading = CapSparL

        constraints = [I <= 2*w*t*(hin/2)**2,
                       dm >= rhocfrp*w*t*b/(self.N-1),
                       W >= 2*dm.sum()*g,
                       w <= w_lim*cave,
                       cave*tau >= hin + 2*t,
                       E == E,
                      ]

        Model.__init__(self, None, constraints, **kwargs)

class CapSparL(Model):
    "spar loading model"
    def __init__(self, static, Wcent, **kwargs):

        Nmax = Variable("N_{max}", 5, "-", "max loading")
        cbar = c_bar(0.5, static.N)
        sigmacfrp = Variable("\\sigma_{CFRP}", 475e6, "Pa", "CFRP max stress")
        kappa = Variable("\\kappa", 0.2, "-", "max tip deflection ratio")
        with vectorize(static.N-1):
            Mr = Variable("M_r", "N*m", "wing section root moment")

        beam = Beam(static.N, cbar)

        constraints = [
            # dimensionalize moment of inertia and young's modulus
            beam["\\bar{EI}"] <= (8*static["E"]*static["I"]/Nmax
                                  / Wcent/static["b"]**2),
            Mr == (beam["\\bar{M}"][:-1]*Wcent*Nmax*static["b"]/4),
            sigmacfrp >= Mr*(static["h_{in}"]+static["t"])/static["I"],
            beam["\\bar{\\delta}"][-1] <= kappa,
            ]

        Model.__init__(self, None, [beam, constraints], **kwargs)

class Beam(Model):
    "discretized beam bending model"
    def __init__(self, N, q, **kwargs):

        with vectorize(N-1):
            EIbar = Variable("\\bar{EI}", "-",
                             "normalized YM and moment of inertia")

        with vectorize(N):
            qbar = Variable("\\bar{q}", q, "-", "normalized loading")
            Sbar = Variable("\\bar{S}", "-", "normalized shear")
            Mbar = Variable("\\bar{M}", "-", "normalized moment")
            th = Variable("\\theta", "-", "deflection slope")
            dbar = Variable("\\bar{\\delta}", "-", "normalized displacement")


        Sbartip = Variable("\\bar{S}_{tip}", 1e-10, "-", "Tip loading")
        Mbartip = Variable("\\bar{M}_{tip}", 1e-10, "-", "Tip moment")
        throot = Variable("\\theta_{root}", 1e-10, "-", "Base angle")
        dbarroot = Variable("\\bar{\\delta}_{root}", 1e-10, "-",
                            "Base deflection")
        dx = Variable("dx", "-", "normalized length of element")

        constraints = [
            Sbar[:-1] >= Sbar[1:] + 0.5*dx*(qbar[:-1] + qbar[1:]),
            Sbar[-1] >= Sbartip,
            Mbar[:-1] >= Mbar[1:] + 0.5*dx*(Sbar[:-1] + Sbar[1:]),
            Mbar[-1] >= Mbartip,
            th[0] >= throot,
            th[1:] >= th[:-1] + 0.5*dx*(Mbar[1:] + Mbar[:-1])/EIbar,
            dbar[0] >= dbarroot,
            dbar[1:] >= dbar[:-1] + 0.5*dx*(th[1:] + th[:-1]),
            1 == (N-1)*dx,
            ]

        Model.__init__(self, None, constraints, **kwargs)


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

class FuelTank(Model):
    """
    Returns the weight of the fuel tank.  Assumes a cylinder shape with some
    fineness ratio
    """
    def __init__(self, Wfueltot, **kwargs):

        W = Variable("W", "lbf", "fuel tank weight")
        f = Variable("f", 0.03, "-", "fraction fuel tank weight to fuel weight")
        mfac = Variable("m_{fac}", 1.1, "-", "fuel volume margin factor")
        rhofuel = Variable("\\rho_{fuel}", 6.01, "lbf/gallon",
                           "density of 100LL")
        Vol = Variable("\\mathcal{V}", "ft^3", "fuel tank volume")

        constraints = [W >= f*Wfueltot,
                       Vol/mfac >= Wfueltot/rhofuel,
                      ]

        Model.__init__(self, None, constraints, **kwargs)

class Fuselage(Model):
    "The thing that carries the fuel, engine, and payload"
    def __init__(self, Wfueltot, **kwargs):

        d = Variable("d", "ft", "fuselage diameter")
        l = Variable("l", "ft", "fuselage length")
        S = Variable("S", "ft^2", "Fuselage surface area")
        Volavn = Variable("\\mathcal{V}_{avn}", 0.125, "ft^3",
                          "Avionics volume")
        W = Variable("W", "lbf", "Fuselage weight")
        mfac = Variable("m_{fac}", 2.1, "-", "Fuselage weight margin factor")
        hengine = Variable("h_{engine}", 6, "in", "engine height")
        phi = Variable("\\phi", 6, "-", "fuselage fineness ratio")

        self.fueltank = FuelTank(Wfueltot)
        self.skin = FuselageSkin(S, d, l)
        self.components = [self.fueltank, self.skin]
        self.flight_model = FuselageAero
        self.loading = FuselageLoading

        constraints = [
            phi == l/d,
            S >= np.pi*d*l + np.pi*d**2,
            np.pi*(d/2)**2*l >= self.fueltank["\\mathcal{V}"] + Volavn,
            d >= hengine,
            W/mfac >= self.fueltank["W"] + self.skin["W"],
            ]

        Model.__init__(self, None, [self.components, constraints], **kwargs)

class FuselageLoading(Model):
    "fuselage loading cases"
    def __init__(self, fuselage, Wcent):

        skinloading = fuselage.skin.loading(fuselage.skin, Wcent)

        Model.__init__(self, None, skinloading)

class FuselageSkin(Model):
    "fuselage skin model"
    def __init__(self, S, d, l):

        W = Variable("W", "lbf", "fuselage skin weight")
        g = Variable("g", 9.81, "m/s^2", "Gravitational acceleration")
        rhokevlar = Variable("\\rho_{kevlar}", 1.3629, "g/cm**3",
                             "kevlar density")
        t = Variable("t", "in", "skin thickness")
        tmin = Variable("t_{min}", 0.03, "in", "minimum skin thickness")
        I = Variable("I", "m**4", "wing skin moment of inertia")

        self.loading = FuselageSkinL

        constraints = [W >= S*rhokevlar*t*g,
                       t >= tmin,
                       I <= np.pi*(d/2)**3*t,
                       l == l]

        Model.__init__(self, None, constraints)

class FuselageSkinL(Model):
    "fuselage skin loading"
    def __init__(self, static, Wcent):

        Mh = Variable("M_h", "N*m", "horizontal axis center fuselage moment")
        Nmax = Variable("N_{max}", 5, "-", "max loading")
        sigmakevlar = Variable("\\sigma_{Kevlar}", 190, "MPa",
                               "stress strength of Kevlar")

        constraints = [Mh >= Nmax*Wcent/4*static["l"],
                       sigmakevlar >= Mh*static["d"]/2/static["I"]]

        Model.__init__(self, None, constraints)

class FuselageAero(Model):
    "fuselage drag model"
    def __init__(self, static, state, **kwargs):

        Cf = Variable("C_f", "-", "fuselage skin friction coefficient")
        Re = Variable("Re", "-", "fuselage reynolds number")

        constraints = [
            Re == state["V"]*state["\\rho"]*static["l"]/state["\\mu"],
            Cf >= 0.455/Re**0.3
            ]

        Model.__init__(self, None, constraints, **kwargs)

class Empennage(Model):
    "empennage model, consisting of vertical, horizontal and tailboom"
    def __init__(self, **kwargs):
        mfac = Variable("m_{fac}", 1.0, "-", "Tail weight margin factor")
        W = Variable("W", "lbf", "empennage weight")

        self.horizontaltail = HorizontalTail()
        self.verticaltail = VerticalTail()
        self.tailboom = TailBoom()
        self.components = [self.horizontaltail, self.verticaltail,
                           self.tailboom]

        self.loading = EmpennageLoading

        constraints = [
            W/mfac >= (self.horizontaltail["W"] + self.verticaltail["W"]
                       + self.tailboom["W"]),
            self.tailboom["l"] >= self.horizontaltail["l_h"],
            self.tailboom["l"] >= self.verticaltail["l_v"],
            ]

        Model.__init__(self, None, [self.components, constraints],
                       **kwargs)

class HorizontalTail(Model):
    "horizontal tail model"
    def __init__(self, **kwargs):
        Sh = Variable("S", "ft**2", "horizontal tail area")
        Vh = Variable("V_h", "-", "horizontal tail volume coefficient")
        ARh = Variable("AR_h", "-", "horizontal tail aspect ratio")
        Abar = Variable("\\bar{A}_{NACA0008}", 0.0548, "-",
                        "cross sectional area of NACA 0008")
        rhofoam = Variable("\\rho_{foam}", 1.5, "lbf/ft^3",
                           "Density of formular 250")
        rhoskin = Variable("\\rho_{skin}", 0.1, "g/cm**2",
                           "horizontal tail skin density")
        bh = Variable("b_h", "ft", "horizontal tail span")
        W = Variable("W", "lbf", "horizontal tail weight")
        Vh = Variable("V_h", "-", "horizontal tail volume coefficient")
        g = Variable("g", 9.81, "m/s^2", "Gravitational acceleration")
        lh = Variable("l_h", "ft", "horizontal tail moment arm")
        CLhmin = Variable("(C_{L_h})_{min}", 0.75, "-",
                          "max downlift coefficient")
        mh = Variable("m_h", "-", "horizontal tail span effectiveness")
        cth = Variable("c_{t_h}", "ft", "horizontal tail tip chord")
        lamhfac = Variable("\\lambda_h/(\\lambda_h+1)", 1.0/(1.0+1), "-",
                           "horizontal tail taper ratio factor")
        CLhtmax = Variable("C_{L_{max}}", "-", "maximum CL of horizontal tail")

        self.flight_model = HorizontalTailAero

        constraints = [
            bh**2 == ARh*Sh,
            mh*(1+2/ARh) <= 2*np.pi,
            W >= g*rhoskin*Sh + rhofoam*Sh**2/bh*Abar,
            cth == 2*Sh/bh*lamhfac,
            lh == lh,
            CLhmin == CLhmin,
            CLhtmax == CLhtmax,
            Vh == Vh,
            ]

        Model.__init__(self, None, constraints, **kwargs)

class HorizontalTailAero(Model):
    "horizontal tail aero model"
    def __init__(self, static, state, **kwargs):

        Cf = Variable("C_f", "-", "fuselage skin friction coefficient")
        Re = Variable("Re", "-", "fuselage reynolds number")

        constraints = [
            Re == (state["V"]*state["\\rho"]*static["S"]/static["b_h"]
                   / state["\\mu"]),
            Cf >= 0.455/Re**0.3,
            ]

        Model.__init__(self, None, constraints, **kwargs)

class VerticalTail(Model):
    "vertical tail model"
    def __init__(self, **kwargs):

        W = Variable("W", "lbf", "one vertical tail weight")
        Sv = Variable("S", "ft**2", "total vertical tail surface area")
        Vv = Variable("V_v", 0.025, "-", "vertical tail volume coefficient")
        ARv = Variable("AR_v", "-", "vertical tail aspect ratio")
        bv = Variable("b_v", "ft", "one vertical tail span")
        rhofoam = Variable("\\rho_{foam}", 1.5, "lbf/ft^3",
                           "Density of formular 250")
        rhoskin = Variable("\\rho_{skin}", 0.1, "g/cm**2",
                           "vertical tail skin density")
        Abar = Variable("\\bar{A}_{NACA0008}", 0.0548, "-",
                        "cross sectional area of NACA 0008")
        g = Variable("g", 9.81, "m/s^2", "Gravitational acceleration")
        lv = Variable("l_v", "ft", "horizontal tail moment arm")
        ctv = Variable("c_{t_v}", "ft", "vertical tail tip chord")
        lamvfac = Variable("\\lambda_v/(\\lambda_v+1)", 1.0/(1.0+1), "-",
                           "vertical tail taper ratio factor")
        CLvtmax = Variable("C_{L_{max}}", 1.1, "-",
                           "maximum CL of vertical tail")
        lantenna = Variable("l_{antenna}", 13.4, "in", "antenna length")
        wantenna = Variable("w_{antenna}", 10.2, "in", "antenna width")

        self.flight_model = VerticalTailAero

        constraints = [Vv == Vv,
                       lv == lv,
                       bv**2 == ARv*Sv,
                       W >= rhofoam*Sv**2/bv*Abar + g*rhoskin*Sv,
                       ctv == 2*Sv/bv*lamvfac,
                       ctv >= wantenna*1.3,
                       bv >= lantenna,
                       CLvtmax == CLvtmax,
                      ]

        Model.__init__(self, None, constraints, **kwargs)

class VerticalTailAero(Model):
    "horizontal tail aero model"
    def __init__(self, static, state, **kwargs):

        Cf = Variable("C_f", "-", "fuselage skin friction coefficient")
        Re = Variable("Re", "-", "fuselage reynolds number")

        constraints = [
            Re == (state["V"]*state["\\rho"]*static["S"]/static["b_v"]
                   / state["\\mu"]),
            Cf >= 0.455/Re**0.3,
            ]

        Model.__init__(self, None, constraints, **kwargs)


class TailBoom(Model):
    "tail boom model"
    def __init__(self, **kwargs):

        l = Variable("l", "ft", "tail boom length")
        E = Variable("E", 150e9, "N/m^2", "young's modulus carbon fiber")
        k = Variable("k", 0.8, "-", "tail boom inertia value")
        kfac = Variable("(1-k/2)", 1-k.value/2, "-", "(1-k/2)")
        I0 = Variable("I_0", "m^4", "tail boom moment of inertia")
        d0 = Variable("d_0", "ft", "tail boom diameter")
        t0 = Variable("t_0", "mm", "tail boom thickness")
        tmin = Variable("t_{min}", 0.25, "mm", "minimum tail boom thickness")
        rhocfrp = Variable("\\rho_{CFRP}", 1.6, "g/cm^3", "density of CFRP")
        g = Variable("g", 9.81, "m/s^2", "Gravitational acceleration")
        W = Variable("W", "lbf", "tail boom weight")
        J = Variable("J", "m^4", "tail boom polar moment of inertia")
        S = Variable("S", "ft**2", "tail boom surface area")

        self.case = TailBoomState()
        self.flight_model = TailBoomAero
        self.horizontalbending = HorizontalBoomBending
        self.verticalbending = VerticalBoomBending
        self.verticaltorsion = VerticalBoomTorsion

        constraints = [
            I0 <= np.pi*t0*d0**3/8.0,
            W >= np.pi*g*rhocfrp*d0*l*t0*kfac,
            t0 >= tmin,
            J <= np.pi/8.0*d0**3*t0,
            S == l*np.pi*d0,
            k == k,
            E == E
            ]

        Model.__init__(self, None, constraints, **kwargs)

class TailBoomFlexibility(Model):
    "tail boom flexibility model"
    def __init__(self, htail, tailboom, wing, state, **kwargs):

        Fne = Variable("F_{NE}", "-", "tail boom flexibility factor")
        deda = Variable("d\\epsilon/d\\alpha", "-", "wing downwash derivative")
        SMcorr = Variable("SM_{corr}", 0.35, "-", "corrected static margin")

        # signomial helper variables
        sph1 = Variable("sph1", "-", "first term involving $V_h$")
        sph2 = Variable("sph2", "-", "second term involving $V_h$")

        constraints = [
            Fne >= (1 + htail["m_h"]*0.5*state["V_{NE}"]**2*state["\\rho_{sl}"]
                    * htail["S"]*tailboom["l"]**2/tailboom["E"]
                    / tailboom["I_0"]*tailboom["(1-k/2)"]),
            sph1*(wing["m_w"]*Fne/htail["m_h"]/htail["V_h"]) + deda <= 1,
            sph2 <= htail["V_h"]*htail["(C_{L_h})_{min}"]/wing["C_{L_{max}}"],
            (sph1 + sph2).mono_lower_bound({"sph1": .48, "sph2": .52}) >= (
                SMcorr + wing["C_M"]/wing["C_{L_{max}}"]),
            deda >= wing["m_w"]*wing["S"]/wing["b"]/4/np.pi/htail["l_h"]]

        Model.__init__(self, None, constraints, **kwargs)

class TailBoomAero(Model):
    "horizontal tail aero model"
    def __init__(self, static, state, **kwargs):

        Cf = Variable("C_f", "-", "fuselage skin friction coefficient")
        Re = Variable("Re", "-", "fuselage reynolds number")

        constraints = [
            Re == (state["V"]*state["\\rho"]*static["l"]/state["\\mu"]),
            Cf >= 0.455/Re**0.3,
            ]

        Model.__init__(self, None, constraints, **kwargs)

class TailBoomState(Model):
    "tail boom design state"
    def __init__(self, **kwargs):

        rhosl = Variable("\\rho_{sl}", 1.225, "kg/m^3",
                         "air density at sea level")
        Vne = Variable("V_{NE}", 40, "m/s", "never exceed vehicle speed")

        constraints = [rhosl == rhosl,
                       Vne == Vne]

        Model.__init__(self, None, constraints, **kwargs)

class EmpennageLoading(Model):
    "tail boom loading case"
    def __init__(self, empennage, **kwargs):
        state = TailBoomState()

        loading = [empennage.tailboom.horizontalbending(
            empennage.tailboom, empennage.horizontaltail, state)]
        loading.append(empennage.tailboom.verticalbending(
            empennage.tailboom, empennage.verticaltail, state))
        loading.append(empennage.tailboom.verticaltorsion(
            empennage.tailboom, empennage.verticaltail, state))

        Model.__init__(self, None, loading, **kwargs)

class VerticalBoomTorsion(Model):
    "tail boom torison case"
    def __init__(self, tailboom, vtail, state, **kwargs):

        T = Variable("T", "N*m", "vertical tail moment")
        taucfrp = Variable("\\tau_{CFRP}", 210, "MPa", "torsional stress limit")

        constraints = [
            T >= (0.5*state["\\rho_{sl}"]*state["V_{NE}"]**2*vtail["S"]
                  * vtail["C_{L_{max}}"]*vtail["b_v"]),
            taucfrp >= T*tailboom["d_0"]/2/tailboom["J"]
            ]

        Model.__init__(self, None, constraints, **kwargs)

class VerticalBoomBending(Model):
    "tail boom bending loading case"
    def __init__(self, tailboom, vtail, state, **kwargs):

        F = Variable("F", "N", "vertical tail force")
        th = Variable("\\theta", "-", "tail boom deflection angle")
        thmax = Variable("\\theta_{max}", 0.3, "-",
                         "max tail boom deflection angle")

        constraints = [
            F >= (0.5*state["\\rho_{sl}"]*state["V_{NE}"]**2*vtail["S"]
                  * vtail["C_{L_{max}}"]),
            th >= (F*tailboom["l"]**2/tailboom["E"]/tailboom["I_0"]
                   * (1+tailboom["k"])/2),
            th <= thmax,
            ]

        Model.__init__(self, None, constraints, **kwargs)

class HorizontalBoomBending(Model):
    "tail boom bending loading case"
    def __init__(self, tailboom, htail, state, **kwargs):

        F = Variable("F", "N", "horizontal tail force")
        th = Variable("\\theta", "-", "tail boom deflection angle")
        thmax = Variable("\\theta_{max}", 0.3, "-",
                         "max tail boom deflection angle")

        constraints = [
            F >= (0.5*state["\\rho_{sl}"]*state["V_{NE}"]**2*htail["S"]
                  * htail["C_{L_{max}}"]),
            th >= (F*tailboom["l"]**2/tailboom["E"]/tailboom["I_0"]
                   * (1+tailboom["k"])/2),
            th <= thmax,
            ]

        Model.__init__(self, None, constraints, **kwargs)

class Mission(Model):
    "creates flight profile"
    def __init__(self, DF70=False, **kwargs):

        mtow = Variable("MTOW", "lbf", "max-take off weight")
        Wcent = Variable("W_{cent}", "lbf", "center aircraft weight")
        Wfueltot = Variable("W_{fuel-tot}", "lbf", "total aircraft fuel weight")

        JHO = Aircraft(Wfueltot, DF70)
        loading = JHO.loading(JHO, Wcent)

        climb1 = Climb(10, JHO, alt=np.linspace(0, 15000, 11)[1:], etap=0.508)
        cruise1 = Cruise(1, JHO, etap=0.684, R=180)
        loiter1 = Loiter(5, JHO, etap=0.647, onStation=True)
        cruise2 = Cruise(1, JHO, etap=0.684)
        mission = [climb1, cruise1, loiter1, cruise2]

        constraints = [
            mtow >= JHO["W_{zfw}"] + Wfueltot,
            Wfueltot >= sum(fs["W_{fuel-fs}"] for fs in mission),
            mission[-1]["W_{end}"][-1] >= JHO["W_{zfw}"],
            Wcent >= Wfueltot + sum(summing_vars(JHO.smeared_loads, "W"))
            ]

        for i, fs in enumerate(mission[1:]):
            constraints.extend([
                mission[i]["W_{end}"][-1] == fs["W_{start}"][0]
                ])

        Model.__init__(self, mtow, [JHO, mission, loading, constraints],
                       **kwargs)


if __name__ == "__main__":
    M = Mission(DF70=True)
    # JHO.debug(solver="mosek")
    sol = M.solve("mosek")
    print sol.table()
