from gpkit import Variable, Model, SignomialsEnabled, LinkedConstraintSet
from gpkit.constraints.costed import CostedConstraintSet
from gpkit.constraints.tight import TightConstraintSet as TCS
from numpy import cos, pi, tan
from wingbox import WingBox
# pylint:disable=bad-whitespace

class Wing(CostedConstraintSet):
    """
    Wing sizing
    """
    def __init__(self, **kwargs):
        Afuel   = Variable('\\bar{A}_{fuel, max}', '-', 'Non-dim. fuel area')
        AR      = Variable('AR_w', '-', 'Wing aspect ratio')
        CDp     = Variable('C_{D_{p_w}}', '-',
                           'Wing parasitic drag coefficient')
        CDw     = Variable('C_{D_w}', '-', 'Drag coefficient, wing')
        CLaw    = Variable('C_{L_{aw}}', '-', 'Lift curve slope, wing')
        CLw     = Variable('C_{L_w}', '-', 'Lift coefficient, wing')
        CLwmax  = Variable('C_{L_{wmax}}', '-', 'Max lift coefficient, wing')
        D       = Variable('D_{wing}', 'N', 'Wing drag')
        Lmax    = Variable('L_{max_{w}}', 'N', 'Maximum load')
        Lw      = Variable('L_w', 'N', 'Wing lift')
        M       = Variable('M', '-', 'Cruise Mach number')
        Re      = Variable('Re_w', '-', 'Cruise Reynolds number (wing)')
        Sw      = Variable('S_w', 'm^2', 'Wing area')
        Vinf    = Variable('V_{\\infty}', 'm/s', 'Freestream velocity')
        Vfuel   = Variable('V_{fuel, max}', 'm^3', 'Available fuel volume')
        Vne     = Variable('V_{ne}', 'm/s', 'Never exceed velocity')
        W       = Variable('W', 'N', 'Aircraft weight')
        W0      = Variable('W_0', 'N', 'Weight excluding wing')
        Wfuel   = Variable('W_{fuel}', 'N', 'Fuel weight')
        Wfuelmax= Variable('W_{fuel,max}', 'N', 'Max fuel weight')
        Ww      = Variable('W_{wing}', 'N', 'Wing weight')
        a       = Variable('a', 'm/s', 'Speed of sound (35,000 ft)')
        alpha   = Variable('\\alpha_w', '-', 'Wing angle of attack')
        amax    = Variable('\\alpha_{max,w}', '-', 'Max angle of attack')
        b       = Variable('b_w', 'm', 'Wing span')
        cosL    = Variable('\\cos(\\Lambda)', '-',
                           'Cosine of quarter-chord sweep angle')
        croot   = Variable('c_{root}', 'm', 'Wing root chord')
        ctip    = Variable('c_{tip}', 'm', 'Wing tip chord')
        cwma    = Variable('\\bar{c}_w', 'm',
                           'Mean aerodynamic chord (wing)')
        e       = Variable('e', '-', 'Oswald efficiency factor')
        eta     = Variable('\\eta_w', '-',
                           'Lift efficiency (diff b/w sectional, actual lift)')
        fl      = Variable('f(\\lambda_w)', '-',
                           'Empirical efficiency function of taper')
        g       = Variable('g', 'm/s^2', 'Gravitational acceleration')
        mu      = Variable('\\mu', 'N*s/m^2', 'Dynamic viscosity (35,000 ft)')
        p       = Variable('p_w', '-', 'Substituted variable = 1 + 2*taper')
        q       = Variable('q_w', '-', 'Substituted variable = 1 + taper')
        rho     = Variable('\\rho', 'kg/m^3', 'Air density (cruise)')
        rho0    = Variable('\\rho_0', 'kg/m^3', 'Air density (0 ft)')
        rhofuel = Variable('\\rho_{fuel}', 'kg/m^3', 'Density of fuel')
        tanL    = Variable('\\tan(\\Lambda)', '-',
                           'Tangent of quarter-chord sweep angle')
        taper   = Variable('\\lambda', '-', 'Wing taper ratio')
        tau     = Variable('\\tau_w', '-', 'Wing thickness/chord ratio')
        tcap    = Variable('t_{cap}' ,'-', 'Non-dim. spar cap thickness')
        tweb    = Variable('t_{web}', '-', 'Non-dim. shear web thickness')
        w       = Variable('w', 0.5, '-', 'Wingbox-width-to-chord ratio')
        #xw     = Variable('x_w', 'm', 'Position of wing aerodynamic center')
        ymac    = Variable('y_{\\bar{c}_w}', 'm',
                           'Spanwise location of mean aerodynamic chord')


        objective = D

        with SignomialsEnabled():
            constraints = [
                           Lw == 0.5*rho*Vinf**2*Sw*CLw,

                           p >= 1 + 2*taper,
                           2*q >= 1 + p,
                           ymac == (b/3)*q/p,
                           TCS([(2./3)*(1+taper+taper**2)*croot/q <= cwma],
                               reltol=1E-2),
                           taper == ctip/croot,
                           TCS([Sw <= b*(croot + ctip)/2], reltol=1E-2), # [SP]

                           # DATCOM formula (Mach number makes it SP)
                           TCS([(AR/eta)**2*(1 + tanL**2 - M**2) + 8*pi*AR/CLaw
                                <= (2*pi*AR/CLaw)**2]),
                           CLw == CLaw*alpha,
                           alpha <= amax,

                           # Drag
                           D == 0.5*rho*Vinf**2*Sw*CDw,
                           CDw >= CDp + CLw**2/(pi*e*AR),
                           Re == rho*Vinf*cwma/mu,
                           1 >= (2.56*CLw**5.88/(Re**1.54*tau**3.32*CDp**2.62)
                              + 3.8e-9*tau**6.23/(CLw**0.92*Re**1.38*CDp**9.57)
                              + 2.2e-3*Re**0.14*tau**0.033/(CLw**0.01*CDp**0.73)
                              + 6.14e-6*CLw**6.53/(Re**0.99*tau**0.52*CDp**5.19)
                              + 1.19e4*CLw**9.78*tau**1.76/(Re*CDp**0.91)),

                           # Oswald efficiency
                           # Nita, Scholz, "Estimating the Oswald factor from
                           # basic aircraft geometrical parameters"
                           TCS([fl >= 0.0524*taper**4 - 0.15*taper**3
                                    + 0.1659*taper**2 - 0.0706*taper + 0.0119],
                               reltol=1E-2),
                           TCS([e*(1 + fl*AR) <= 1]),
                           taper >= 0.2, # TODO

                           Lmax == 0.5*rho0*Vne**2*Sw*CLwmax,

                           # Fuel volume [TASOPT doc]
                           Afuel <= w*0.92*tau,
                           # GP approx of the signomial constraint:
                           # Afuel <= (w - 2*tweb)*(0.92*tau - 2*tcap),
                           Vfuel <= croot**2 * (b/6) * (1+taper+taper**2)*cosL,
                           Wfuel <= rhofuel*Afuel*Vfuel*g,
                          ]

            standalone_constraints = [W >= W0 + Ww + Wfuel,
                                      Lw == W,
                                      M == Vinf/a,
                                      ]

            self.standalone_constraints = standalone_constraints

        wb = WingBox()
        wb.subinplace({'A': AR,
                       'b': b,
                       'L_{max}': Lmax,
                       'p': p,
                       'q': q,
                       'S': Sw,
                       'taper': taper,
                       '\\tau': tau,
                       'W_{struct}': Ww})

        lc = LinkedConstraintSet([constraints, wb])

        CostedConstraintSet.__init__(self, objective, lc, **kwargs)

    def default737subs(self):

        sweep = 30 # [deg]

        substitutions = {
                         'C_{L_{wmax}}': 2.5,
                         'M': 0.78,
                         'V_{ne}': 144,
                         'W_0': 5E5,
                         'W_{fuel}': 1E5,
                         '\\alpha_{max,w}': 0.1, # (6 deg)
                         '\\cos(\\Lambda)': cos(sweep*pi/180),
                         '\\eta_w': 0.97,
                         '\\mu': 1.4E-5,
                         '\\rho': 0.38,
                         '\\rho_0': 1.225,
                         '\\rho_{fuel}': 817, # Kerosene [TASOPT]
                         '\\tan(\\Lambda)': tan(sweep*pi/180),
                         'a': 297,
                         'g': 9.81,
                        }

        return substitutions

    @classmethod
    def standalone737(cls):
        ccs = cls()

        constraints = ccs + ccs.standalone_constraints

        substitutions = ccs.default737subs()

        m = Model(ccs.cost, constraints, substitutions)
        return m

    @classmethod
    def coupled737(cls):
        ccs = cls()

        dsubs = ccs.default737subs()
        del dsubs['a']
        linkedsubs = ['M', 'W_0', 'W_{fuel}']
        substitutions = {key: value for key, value in dsubs.items()
                                    if key not in linkedsubs}

        m = Model(ccs.cost, ccs, substitutions, name='Wing')
        return m

    @classmethod
    def test(cls):
        w = cls.standalone737()
        sol = w.localsolve()
        print sol.table()

if __name__ == "__main__":
    Wing.test()
