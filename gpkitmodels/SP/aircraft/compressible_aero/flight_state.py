"""Flight state model."""

from gpkit import Model, Variable, units
from gpkit import SignomialsEnabled, SignomialEquality
from gpkit.constraints.tight import Tight
from gpkit.constraints.loose import Loose

class FlightState(Model):
    def setup(self):
        mach_fixed = True

        ### Declare Geometric Programming variables ###
        mach = Variable('mach', '', 'Freestream Mach number')
        p_dyn = Variable('p_dyn', 'pascal', 'Freestream dynamic pressure')
        p_static = Variable('p_static', 30e3, 'pascal', 'Freestream static pressure')
        gamma_air = Variable('gamma_air', 1.40, '', 'Ratio of specific heats of air')
        if mach_fixed:
            beta_pg = Variable('beta_pg',
                               lambda c: (1 - c[mach]**2)**0.5, '', 'Prandtl-Glauert beta parameter')
        else:
            beta_pg = Variable('beta_pg', '', 'Prandtl-Glauert beta parameter')
        ### Declare Geometric Programming constraints. ###
        # Dynamic pressure
        # Source: https://en.wikipedia.org/wiki/Dynamic_pressure#Compressible_flow
        constraints = [
            p_dyn == 0.5 * gamma_air * p_static * mach**2,

            # Limit on Mach number range of model
            Loose([mach <= 1]),
        ]

        # TODO put constraints on beta instead of making it derived,
        # in case we ever want to optimize over Mach number
        # Matt emailed Ned asking how to do this on 2019-03-11
        if not mach_fixed:
            with SignomialsEnabled():
                constraints += [
                    # Prandtl-Glauert parameter for subsonic flow.
                    Tight([beta_pg**2 >= 1 - mach**2]),
                    # SignomialEquality(beta_pg**2, 1 - mach**2),
                ]
        return constraints
