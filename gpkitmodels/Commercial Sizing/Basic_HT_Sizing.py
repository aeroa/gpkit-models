from gpkit import Variable, Model, units, SignomialsEnabled
from gpkit.constraints.sigeq import SignomialEqualityConstraint as SignomialEquality
from numpy import pi
from gpkit.constraints.tight import TightConstraintSet as TCS
import matplotlib.pyplot as plt
import numpy as np

class BasicHT(Model):
    """
    Basic horizontal tail sizing model. Given a CG travel range the
    model enforces a minium static margin for aft CG and pitch trim
    at forward CG and max lift.
    """
    def __init__(self, substitutions):
        #define variables
        #weight variables
        W_wing = Variable('W_{wing}', 'N', 'Wing Weight')
        W_HT = Variable('W_{HT}', 'N', 'Horizontal Tail Weight')
        W_payload = Variable('W_{payload}', 'N', 'Payload Weight')
        W_fuel = Variable('W_{fuel}', 'N', 'Fuel Weight')
        W_start = Variable('W_{start}', 'N', 'Segment Start Weight')
        W_end = Variable('W_{end}', 'N', 'Segment End Weight')
        W_avg = Variable('W_{avg}', 'N', 'Average Segment Weight')

        #wing geometry
        S = Variable('S', 'm^2', 'Wing Planform Area')
        AR = Variable('AR', '-', 'Aspect Ratio')
        b = Variable('b', 'm', 'Wing Span')
        b_max = Variable('b_{max}', 'm', 'Max Wing Span')
        MAC = Variable('MAC', 'm', 'Mean Aerodynamic Chord')

        #HT geometry
        Sh = Variable('Sh', 'm^2', 'HT Planform Area')
        ARh = Variable('ARh', '-', 'HT Aspect Ratio')
        Vh = Variable('V_{h}', '-', 'Horizontal Tail Volume Coefficient')
        bh = Variable('b_{h}', 'm', 'HT Span')
        MACh = Variable('MAC_{h}', 'm', 'HT Mean Aerodynamic Chord')

        #aircraft geometry
        lfuse = Variable('l_{fuse}', 'm', 'Fuselage Length')
        lh = Variable('l_{h}', 'm', 'Horizontal Tail Location')

        #Moments
        cmw = Variable('c_{m_{w}}', '-', 'Wing Pitching Moment Coefficient')   #approximtaed as a constant via TAT

        #aero
        L = Variable('L', 'N', 'Wing Lift')
        L_h = Variable('L_{h}', 'N', 'Horizontal Tail Downforce')
        CLmax = Variable('C_{L_{max}}', '-', 'Max Wing Lift Coefficient')
        CL = Variable('C_{L}', '-', 'Wing Lift Coefficient')
        CLhmax = Variable('CL_{h_{max}}', '-', 'Max Tail Downforce Coefficient')
        CLh = Variable('C_{L_{h}}', '-', 'Tail Downforce Coefficient')
        D = Variable('D', 'N', 'Drag')
        Cd0 = Variable('C_{D_{0}}', '-', 'Profile Drag')
        alpha = Variable('\\alpha', '-', 'Angle of Attack')
        K = Variable('K', '-', 'Induced Drag Parameter')
        e = Variable('e', '-', 'Oswald Efficiency')
        Kh = Variable('Kh', '-', 'HT Induced Drag Parameter')
        mrat = Variable('m_{ratio}', '-', 'Wing to Tail Lift Slope Ratio')

        #atm
        rho = Variable('\\rho', 'kg/m^3', 'Air Density')

        #airspeed
        V = Variable('V', 'm/s', 'Airspeed')

        #min static margin
        SMmin = Variable('SM_{min}', '-', 'Minimum Static Margin')
        dxcg = Variable('\\Delta x_{CG}', 'm', 'Max CG Travel Range')

        #make the constraints
        constraints = []

        with SignomialsEnabled():

            constraints.extend([
                #wing weight constraint
                #based off of a raymer weight and 737 data from TASOPT output file
                (S/(124.58*units('m^2')))**.65 == W_wing/(105384.1524*units('N')),

                #HT weight constraint
                #based off of a raymer weight and 737 data from TASOPT output file
                (Sh/(46.1*units('m^2')))**.65 == W_HT/(16064.7523*units('N')),

                #Wing geometry
                S == b*MAC,
                AR == b/MAC,    
                b <= b_max,

                #HT geometry
                Sh == bh*MACh,
                ARh == bh/MACh,
 
                #drag constraints
                K == 1/(pi*e*AR),
                Kh == 1/(pi*e*ARh),
                D >= .5*rho*S*V**2*(Cd0 + K*CL**2) + .5*rho*Sh*V**2*(Cd0 + Kh*CLh**2),

                #assumes a 2 hour flight w/TSFC = 0.5 hr^-1
                W_fuel == 0.5 * D * 2,    

                #compute the lift
                W_start >= W_wing + W_HT + W_payload + W_fuel,
                W_end >= W_wing + W_HT + W_payload,
                W_avg == (W_start*W_end)**.5,
                L >= W_avg + L_h,
                L == .5 * rho * V**2 * S * CL,
                L_h == .5 * rho * V**2 * Sh * CLh,

                #lift coefficient constraints
                CL == 2*pi*alpha,
                CLh <= 2.1*pi*alpha,
                CLh >= 1.9*pi*alpha,
                    
                CL <= CLmax,
                CLh <= CLhmax,

                #compute mrat, is a signomial equality
                SignomialEquality(mrat*(1+2/AR), 1 + 2/ARh),

                #tail volume coefficient
                Vh == Sh*lh/(S*MAC),

                #enforce max tail location is the end of the fuselage
                lh <= lfuse,

                #Stability constraint, is a signomial
                TCS([SMmin + dxcg/MAC <= Vh*mrat + cmw/CLmax + Vh*CLhmax/CLmax]),

                #arbitrary, sturctural model will remove the need for this constraint
                bh <= .33*b_max,
                ])

            Model.__init__(self, W_fuel, constraints, substitutions)

if __name__ == '__main__':
    PLOT = True
    
    substitutions = {
        'W_{payload}': 85100*9.81,
        'b_{max}': 30,
        'l_{fuse}': 30,
        'c_{m_{w}}': 1,
        'C_{L_{max}}': 2,
        'CL_{h_{max}}': 2.5,
        '\\rho': .8,
        'V': 230,
        'SM_{min}': 0.5,
        'C_{D_{0}}': 0.05,
        'e': 0.9,
        '\\Delta x_{CG}': 4,
    }

    m = BasicHT(substitutions)

    sol = m.localsolve(solver="mosek", verbosity=4)

    if PLOT == True:
        #sweeps of cg range
        substitutions = {
            'W_{payload}': 85100*9.81,
            'b_{max}': 30,
            'l_{fuse}': 30,
            'c_{m_{w}}': 1,
            'C_{L_{max}}': 2,
            'CL_{h_{max}}': 2.5,
            '\\rho': .8,
            'V': 230,
            'SM_{min}': 0.5,
            'C_{D_{0}}': 0.05,
            'e': 0.9,
            '\\Delta x_{CG}': ('sweep', np.linspace(.5,6,10)),
        }

        m = BasicHT(substitutions)

        solCGsweep = m.localsolve(solver="mosek", verbosity=1)

        plt.plot(solCGsweep('\\Delta x_{CG}'), solCGsweep('Sh'), '-r')
        plt.xlabel('CG Travel Range [m]')
        plt.ylabel('Horizontal Tail Area [m$^2$]')
        plt.title('Horizontal Tail Area vs CG Travel Range')
        plt.show()

        plt.plot(solCGsweep('\\Delta x_{CG}'), solCGsweep('V_{h}'), '-r')
        plt.xlabel('CG Travel Range [m]')
        plt.ylabel('Horizontal Tail Volume Coefficient')
        plt.title('Horizontal Tail Area vs CG Travel Range')
        plt.show()

        #sweeps of SMmin
        substitutions = {
            'W_{payload}': 85100*9.81,
            'b_{max}': 30,
            'l_{fuse}': 30,
            'c_{m_{w}}': 1,
            'C_{L_{max}}': 2,
            'CL_{h_{max}}': 2.5,
            '\\rho': .8,
            'V': 230,
            'SM_{min}': ('sweep', np.linspace(.05,1,10)),
            'C_{D_{0}}': 0.05,
            'e': 0.9,
            '\\Delta x_{CG}': 2,
        }

        m = BasicHT(substitutions)

        solSMsweep = m.localsolve(solver="mosek", verbosity=1)

        plt.plot(solSMsweep('SM_{min}'), solSMsweep('Sh'), '-r')
        plt.xlabel('Minimum Allowed Static Margin')
        plt.ylabel('Horizontal Tail Area [m$^2$]')
        plt.title('Horizontal Tail Area vs Min Static Margin')
        plt.show()

        plt.plot(solSMsweep('SM_{min}'), solSMsweep('V_{h}'), '-r')
        plt.xlabel('Minimum Allowed Static Margin')
        plt.ylabel('Horizontal Tail Volume Coefficient')
        plt.title('Horizontal Tail Volume Coefficient vs Min Static Margin')
        plt.show()

        #sweeps of payload
        substitutions = {
            'W_{payload}': ('sweep', np.linspace(50000*9.81,85100*9.81,10)),
            'b_{max}': 30,
            'l_{fuse}': 30,
            'c_{m_{w}}': 1,
            'C_{L_{max}}': 2,
            'CL_{h_{max}}': 2.5,
            '\\rho': .8,
            'V': 230,
            'SM_{min}': .1,
            'C_{D_{0}}': 0.05,
            'e': 0.9,
            '\\Delta x_{CG}': 2,
        }

        m = BasicHT(substitutions)

        solPayloadsweep = m.localsolve(solver="mosek", verbosity=1)

        plt.plot(solPayloadsweep('W_{payload}'), solPayloadsweep('Sh'), '-r')
        plt.xlabel('Payload Weight [N]')
        plt.ylabel('Horizontal Tail Area [m$^2$]')
        plt.title('Horizontal Tail Area vs Payload Weight')
        plt.show()

        plt.plot(solPayloadsweep('W_{payload}'), solPayloadsweep('V_{h}'), '-r')
        plt.xlabel('Payload Weight [N]')
        plt.ylabel('Horizontal Tail Volume Coefficient')
        plt.title('Horizontal Tail Volume Coefficient vs Payload Weight')
        plt.show()
