import numpy as np
from gpkit import Model, Variable, SignomialsEnabled, units, ConstraintSet, SignomialEquality
from gpkit.constraints.tight import TightConstraintSet as TCS

#Cp and gamma values estimated from https://www.ohio.edu/mechanical/thermo/propeRy_tables/air/air_Cp_Cv.html

class FanAndLPC(ConstraintSet):
    """
    Free Stream, Fan, and LPC Calcs for the Engine Model
    """
    def __init__(self, **kwargs):
        #air propeRies
        R = Variable('R', 287, 'J/kg/K', 'R')
        gammaAir = Variable('gamma_{air}', 1.4, '-', 'Specific Heat Ratio for Ambient Air')
        Cpair = Variable('Cp_{air}', 1003, 'J/kg/K', "Cp Value for Air at 250K")
        Cp1 = Variable('Cp_{1}', 1008, 'J/kg/K', "Cp Value for Air at 350K")#gamma = 1.398
        Cp2 = Variable('Cp_{2}', 1099, 'J/kg/K', "Cp Value for Air at 800K") #gamma = 1.354
        c1 = Variable('c1', 1.128, '-', 'Constant in Stagnation Eqn')

        #free stream
        T0 = Variable('T_0', 'K', 'Free Stream Stagnation Temperature')
        P0 = Variable('P_0', 'kPa', 'Free Stream Static Pressure')
        M0 = Variable('M_0', '-', 'Free Stream Mach Number')
        
        #new Vars for free stream
        a0 = Variable('a_0', 'm/s', 'Speed of Sound in Freestream')
        u0 = Variable('u_0', 'm/s', 'Free Stream Speed') 
        Pt0 = Variable('P_{t_0}', 'kPa', 'Free Stream Stagnation Pressure')
        Tt0 = Variable('T_{t_0}', 'K', 'Free Stream Stagnation Temperature')
        ht0 = Variable('h_{t_0}', 'J/kg', 'Free Stream Stagnation Enthalpy')

        #new vars for the diffuser exit
        Pt18 = Variable('P_{t_1.8}', 'kPa', 'Stagnation Pressure at the Diffuser Exit (1.8)')
        Tt18 = Variable('T_{t_1.8}', 'K', 'Stagnation Temperature at the Diffuser Exit (1.8)')
        ht18 = Variable('h_{t_1.8}', 'J/kg', 'Stagnation Enthalpy at the Diffuser Exit (1.8)')
        
        #new vars for the fan inlet
        Pt2 = Variable('P_{t_2}', 'kPa', 'Stagnation Pressure at the Fan Inlet (2)')
        Tt2 = Variable('T_{t_2}', 'K', 'Stagnation Temperature at the Fan Inlet (2)')
        ht2 = Variable('h_{t_2}', 'J/kg', 'Stagnation Enthalpy at the Fan Inlet (2)')

        #new vars for the fan exit (station 2.1)
        Pt21 = Variable('P_{t_2.1}', 'kPa', 'Stagnation Pressure at the Fan Exit (2.1)')
        Tt21 = Variable('T_{t_2.1}', 'K', 'Stagnation Temperature at the Fan Exit (2.1)')
        ht21 = Variable('h_{t_2.1}', 'J/kg', 'Stagnation Enthalpy at the Fan Exit (2.1)')

        #new vars for the LPC exit (station 2.5)
        Pt25 = Variable('P_{t_2.5}', 'kPa', 'Stagnation Pressure at the LPC Exit (2.5)')
        Tt25 = Variable('T_{t_2.5}', 'K', 'Stagnation Temperature at the LPC Exit (2.5)')
        ht25 = Variable('h_{t_2.5}', 'J/kg', 'Stagnation Enthalpy at the LPC Exit (2.5)')

        #HPC exit state variables (station 3)
        Pt3 = Variable('P_{t_3}', 'kPa', 'Stagnation Pressure at the HPC Exit (3)')
        Tt3 = Variable('T_{t_3}', 'K', 'Stagnation Temperature at the HPC Exit (3)')
        ht3 = Variable('h_{t_3}', 'J/kg', 'Stagnation Enthalpy at the HPC Exit (3)')

        #new vars for the fan nozzle exit (station 7)
        Pt7 = Variable('P_{t_7}', 'kPa', 'Stagnation Pressure at the Fan Nozzle Exit (7)')
        Tt7 = Variable('T_{t_7}', 'K', 'Stagnation Temperature at the Fan Nozzle Exit (7)')
        ht7 = Variable('h_{t_7}', 'J/kg', 'Stagnation Enthalpy at the Fan Nozzle Exit (7)')
        
        #fan efficiency variable
        etaFan = Variable('\eta_{fan}', 0.9,'-', 'Fan Polytropic Efficiency')

        #compressor efficiency variables
        etalc = Variable('\eta_{lc}', 0.887,'-', 'Low Pressure Compressor Polytropic Efficiency')
        etahc = Variable('\eta_{hc}', 0.887,'-', 'High Pressure Compressor Polytropic Efficiency')

        #pressure ratios
        pid = Variable('\pi_{d}', '-', 'Diffuser Pressure Ratio')
        pif = Variable('\pi_f', '-', 'Fan Pressure Ratio')
        pifn = Variable('\pi_{fn}', '-', 'Fan Duct Pressure Loss Ratio')
        pilc = Variable('\pi_{lc}', '-', 'LPC Pressure Ratio')
        pihc = Variable('\pi_{hc}', '-', 'HPC Pressure Ratio')

        #constraints
        constraints = [
            #free stream speed of sound and free stream velocity
            a0 == (gammaAir * R*  T0)**.5,        #traceable to B.109
            u0 == M0 * a0,                           #traceable to B.110
            
            #free stream stagnation values
            Pt0 == P0 / (c1 ** -3.5), #https://www.grc.nasa.gov/www/k-12/airplane/isentrop.html
            Tt0 == T0 / (c1) ** (-1),             #https://www.grc.nasa.gov/www/k-12/airplane/isentrop.html
            ht0 == Cpair * Tt0,

            #diffuser exit stagnation values (station 1.8)
            Pt18 == pid * Pt0,  #B.113
            Tt18 == Tt0,        #B.114
            ht18 == ht0,        #B.115

            #fan inlet constraints (station 2)
            Tt2 == Tt18,    #B.120
            ht2 == ht18,    #B.121
            Pt2 == Pt18,
                        
            #fan exit constraints (station 2.1)
            Pt21 == pif * Pt2,  #16.50
            Tt21 == Tt2 * pif ** (.31746),   #16.50
            ht21 == Cpair * Tt21,   #16.50

            #fan nozzle exit (station 7)
            Pt7 == pifn * Pt21,     #B.125
            Tt7 == Tt21,    #B.126
            ht7 == ht21,    #B.127

            #LPC exit (station 2.5)
            Pt25 == pilc * Pt2,
            Tt25 == Tt2 * pilc ** (.320961),
            ht25 == Tt25 * Cp1,

            #HPC Exit
            Pt3 == pihc * Pt25,
            Tt3 == Tt25 * pihc ** (.2947548622),
            ht3 == Cp2 * Tt3
            ]
##        Model.__init__(self, ht3, constraints, **kwargs)
        ConstraintSet.__init__(self, constraints, **kwargs)
        

class CombustorCooling(ConstraintSet):
    """
    class to represent the engine's combustor and perform calculations
    on engine cooling bleed flow...cooling flow is currently not implemented
    """
    def __init__(self, **kwargs):
        #new vars
        #gas propeRies
        Cpc = Variable('Cp_c', 1204, 'J/kg/K', "Cp Value for Fuel/Air Mix in Combustor") #1400K
        
        #HPC exit state variables (station 3)
        Pt3 = Variable('P_{t_3}', 'kPa', 'Stagnation Pressure at the HPC Exit (3)')
        ht3 = Variable('h_{t_3}', 'J/kg', 'Stagnation Enthalpy at the HPC Exit (3)')
        
        #combustor exit state variables..recall Tt4 is already set in Engine class
        Pt4 = Variable('P_{t_4}', 'kPa', 'Stagnation Pressure at the Combustor Exit (4)')
        ht4 = Variable('h_{t_4}', 'J/kg', 'Stagnation Enthalpy at the Combustor Exit (4)')
        Tt4 = Variable('T_{t_4}', 'K', 'Combustor Exit (Station 4) Stagnation Temperature')

        #Turbine inlet state variables (station 4.1)
        Pt41 = Variable('P_{t_4.1}', 'kPa', 'Stagnation Pressure at the Turbine Inlet (4.1)')
        Tt41 = Variable('T_{t_4.1}', 'K', 'Stagnation Temperature at the Turbine Inlet (4.1)')
        ht41 = Variable('h_{t_4.1}', 'J/kg', 'Stagnation Enthalpy at the Turbine Inlet (4.1)')

        #burner pressure ratio
        pib = Variable('\pi_{b}', '-', 'Burner Pressure Ratio')

        #flow faction f
        f = Variable('f', '-', 'Fuel Air Mass Flow Fraction')

        #heat of combustion of jet fuel
        hf = Variable('h_f', 42.8, 'MJ/kg', 'Heat of Combustion of Jet Fuel')     #http://hypeRbook.com/facts/2003/EvelynGofman.shtml...prob need a better source

        with SignomialsEnabled():
        
            constraints = [
                #flow through combustor
                Pt4 == pib * Pt3,   #B.145
                ht4 == Cpc * Tt4,

                #fuel flow fraction f
                TCS([f*hf + ht3 >= ht4]),

                #flow at turbine inlet
                Tt41 == Tt4,
                Pt41 == Pt4,
                ht41 == ht4
                ]
            
##        Model.__init__(self, 1/f, constraints, **kwargs)
        ConstraintSet.__init__(self, constraints, **kwargs)
        

class Turbine(ConstraintSet):
    """
    classs to represent the engine's turbine
    """
    def __init__(self, **kwargs):
        #gas propeRies
        Cpt1 =Variable('Cp_t1', 1190, 'J/kg/K', "Cp Value for Combustion Products in HP Turbine") #1300K gamma = 1.318
        Cpt2 =Variable('Cp_t2', 1099, 'J/kg/K', "Cp Value for Combustion Products in LP Turbine") #800K gamma = 1.354
        
        #new variables
        ht45 = Variable('h_{t_4.5}', 'J/kg', 'Stagnation Enthalpy at the HPT Exit (4.5)')
        Pt45 = Variable('P_{t_4.5}', 'kPa', 'Stagnation Pressure at the HPT Exit (4.5)')
        Tt45 = Variable('T_{t_4.5}', 'K', 'Stagnation Temperature at the HPT Exit (4.5)')

        #enthalpies used in shaft power balances
        ht18 = Variable('h_{t_1.8}', 'J/kg', 'Stagnation Enthalpy at the Diffuser Exit (1.8)')
        ht2 = Variable('h_{t_2}', 'J/kg', 'Stagnation Enthalpy at the Fan Inlet (2)')
        ht21 = Variable('h_{t_2.1}', 'J/kg', 'Stagnation Enthalpy at the Fan Inlet (2.1)')
        ht25 = Variable('h_{t_2.5}', 'J/kg', 'Stagnation Enthalpy at the LPC Exit (2.5)')
        ht3 = Variable('h_{t_3}', 'J/kg', 'Stagnation Enthalpy at the HPC Exit (3)')

        #Turbine inlet state variables (station 4.1)
        Pt41 = Variable('P_{t_4.1}', 'kPa', 'Stagnation Pressure at the Turbine Inlet (4.1)')
        Tt41 = Variable('T_{t_4.1}', 'K', 'Stagnation Temperature at the Turbine Inlet (4.1)')
        ht41 = Variable('h_{t_4.1}', 'J/kg', 'Stagnation Enthalpy at the Turbine Inlet (4.1)')

        #HPT exit states
        Pt49 = Variable('P_{t_4.9}', 'kPa', 'Stagnation Pressure at the HPTExit (49)')
        Tt49 = Variable('T_{t_4.9}', 'K', 'Stagnation Temperature at the HPT Exit (49)')
        ht49 = Variable('h_{t_4.9}', 'J/kg', 'Stagnation Enthalpy at the HPT Exit (49)')
        
        #turbine nozzle exit states
        Pt5 = Variable('P_{t_5}', 'kPa', 'Stagnation Pressure at the Turbine Nozzle Exit (5)')
        Tt5 = Variable('T_{t_5}', 'K', 'Stagnation Temperature at the Turbine Nozzle Exit (5)')
        ht5 = Variable('h_{t_5}', 'J/kg', 'Stagnation Enthalpy at the Turbine Nozzle Exit (5)')

        #pressure ratios
        pihpt = Variable('\pi_{HPT}', '-', 'HPT Pressure Ratio')
        pilpt = Variable('\pi_{LPT}', '-', 'LPT Pressure Ratio')
        
        #turbine efficiences
        etaht = Variable('\eta_{ht}', 0.9, '-', 'Polytropic Efficiency of HPT')
        etalt = Variable('\eta_{lt}', 0.9, '-', 'Polytropic Efficiency of LPT')

        #flow faction f
        f = Variable('f', '-', 'Fuel Air Mass Flow Fraction')

        #BPR
        alpha = Variable('alpha', '-', 'By Pass Ratio')

        #relavent pressure ratio
        pitn = Variable('\pi_{tn}', '-', 'Turbine Nozzle Pressure Ratio')

        with SignomialsEnabled():
            constraints = [
                #HPT shafter power balance
                #SIGNOMIAL   
                SignomialEquality((1+f)*(ht41-ht45),ht3 - ht25),    #B.161

                #LPT shaft power balance
                #SIGNOMIAL  
                SignomialEquality((1+f)*(ht49 - ht45),-((ht25-ht18)+alpha*(ht21 - ht2))),    #B.165

                #HPT Exit states (station 4.5)
                Pt45 == pihpt * Pt41,
                pihpt == (Tt45/Tt41)**(4.60517),      #turbine efficiency is 0.9
                ht45 == Cpt1 * Tt45,

                #LPT Exit States
                Pt49 == pilpt * Pt45,
                pilpt == (Tt49/Tt45)**(4.2498431),    #turbine efficiency is 0.9
                ht49 == Cpt2 * Tt49,

                #turbine nozzle exit states
                Pt5 == pitn * Pt49, #B.167
                Tt5 == Tt49,    #B.168
                ht5 == ht49     #B.169
                ]
##        Model.__init__(self, 1/ht49, constraints, **kwargs)
        ConstraintSet.__init__(self, constraints, **kwargs)
        
class ExhaustAndThrust(ConstraintSet):
    """
    Class to calculate the exhaust quantities as well as
    the overall engine thrust and on design TSFCe & ISP
    """
    def __init__(self, **kwargs):
        
        a0 = Variable('a_0', 'm/s', 'Speed of Sound in Freestream')
        u0 = Variable('u_0', 'm/s', 'Free Stream Speed')
        
        #external atmosphere propeRies
        P0 = Variable('P_0', 'kPa', 'Free Stream Stagnation Pressure')
        
        #gas propeRies
        Cptex =Variable('Cp_tex', 1029, 'J/kg/K', "Cp Value for Combustion Products at Core Exhaust") #500K, gamma = 1.387
        Cpfanex = Variable('Cp_fex', 1005, 'J/kg/K', "Cp Value for Air at 300K") #gamma =1.4
        R = Variable('R', 287, 'J/kg/K', 'R for Air')
        #gravity
        g = Variable('g', 9.81, 'm/(s^2)', 'Gravitational Acceleration')
        
        #fan exhaust variables
        P8 = Variable('P_8', 'kPa', 'Fan Exhaust Static Pressure')
        Pt8 = Variable('P_{t_8}', 'kPa', 'Fan Exhaust Stagnation Pressure')
        ht8 = Variable('h_{t_8}', 'J/kg', 'Fan Exhaust Stagnation Enthalpy')
        h8 = Variable('h_8', 'J/kg', 'Fan Exhasut Static Enthalpy')
        Tt8 = Variable('T_{t_8}', 'K', 'Fan Exhaust Stagnation Temperature (8)')
        T8 = Variable('T_{8}', 'K', 'Fan Exhaust Sttic Temperature (8)')

        #turbine nozzle exit states
        Pt5 = Variable('P_{t_5}', 'kPa', 'Stagnation Pressure at the Turbine Nozzle Exit (5)')
        Tt5 = Variable('T_{t_5}', 'K', 'Stagnation Temperature at the Turbine Nozzle Exit (5)')
        ht5 = Variable('h_{t_5}', 'J/kg', 'Stagnation Enthalpy at the Turbine Nozzle Exit (5)')
        
        #core exit variables
        P6 = Variable('P_6', 'kPa', 'Core Exhaust Static Pressure')
        Pt6 = Variable('P_{t_6}', 'kPa', 'Core Exhaust Stagnation Pressure')
        Tt6 = Variable('T_{t_6}', 'K', 'Core Exhaust Stagnation Temperature (6)')
        T6 = Variable('T_{6}', 'K', 'Core Exhaust Static Temperature (6)')
        ht6 = Variable('h_{t_6}', 'J/kg', 'Core Exhaust Stagnation Enthalpy')
        h6 = Variable('h_6', 'J/kg', 'Core Exhasut Static Enthalpy')

        #new vars for the fan nozzle exit (station 7)
        Pt7 = Variable('P_{t_7}', 'kPa', 'Stagnation Pressure at the Fan Nozzle Exit (7)')
        Tt7 = Variable('T_{t_7}', 'K', 'Stagnation Temperature at the Fan Nozzle Exit (7)')
        ht7 = Variable('h_{t_7}', 'J/kg', 'Stagnation Enthalpy at the Fan Nozzle Exit (7)')

        #thrust variables
        F8 = Variable('F_8', 'N', 'Fan Thrust')
        F6 = Variable('F_6', 'N', 'Core Thrust')
        F = Variable('F', 'N', 'Total Thrust')
        Fsp = Variable('F_{sp}', '-', 'Specific Net Thrust')
        Isp = Variable('I_{sp}', 's', 'Specific Impulse')
        TSFCe = Variable('TSFC_E', '1/hr', 'Thrust Specific Fuel Consumption')

        #exhaust speeds
        u6 = Variable('u_6', 'm/s', 'Core Exhaust Velocity')
        u8 = Variable('u_8', 'm/s', 'Fan Exhaust Velocity')
        u7 = Variable('u_7', 'm/s', 'Station 7 Exhaust Velocity')
        u5 = Variable('u_5', 'm/s', 'Station 5 Exhaust Velocity')

        #BPR
        alpha = Variable('alpha', '-', 'By Pass Ratio')
        alphap1 = Variable('alphap1', '-', '1 plus BPR')

        #core mass flow
        mCore = Variable('m_{core}', 'kg/s', 'Core Mass Flow')

        #flow faction f
        f = Variable('f', '-', 'Fuel Air Mass Flow Fraction')
        fp1 = Variable('fp1', '-', 'f + 1')

        #mach numbers
        M8 = Variable('M_8', '-', 'Fan Exhaust Mach Number')
        M6 = Variable('M_6', '-', 'Core Exhaust Mach Number')
        
        with SignomialsEnabled():
            constraints = [
                Pt8 == Pt7, #B.179
                Tt8 == Tt7, #B.180
                P8 == P0,
                h8 == Cpfanex * T8,
                TCS([u8**2 + 2*h8 <= 2*ht8]),
##                SignomialEquality(u8**2 + 2*h8, 2*ht8),
                (P8/Pt8)**(.2857) == T8/Tt8,
                ht8 == Cpfanex * Tt8,
                
                #core exhaust
                P6 == P0,   #B.4.11 intro
                Pt6 == Pt5, #B.183
                Tt6 == Tt5, #B.184
                (P6/Pt6)**(.387/1.387) == T6/Tt6,
                TCS([u6**2 <= (2*(ht6 -h6))]),
##                TCS([u6**2 >= .5*(2*(ht6 -h6))]),
##                SignomialEquality(u6**2+2*h6, 2*ht6),
                h6 == Cptex * T6,
                ht6 == Cptex * Tt6,

                #mach nubmers for post processing of the data
                M8 == u8/((T8*Cpfanex*R/(781*units('J/kg/K')))**.5),
                M6 == u6/((T6*Cptex*R/(781*units('J/kg/K')))**.5),

                #overall thrust values
##                TCS([F8/(alpha * mCore) + u0 <= u8]),  #B.188
##                TCS([F6/mCore + u0 <= u6]),      #B.189

                #SIGNOMIAL
##                TCS([F  <= F6 + F8]),

                u6 >= u0,
                u8 >= u0,

                F + alphap1*mCore*u0 <= mCore*u6+mCore*alpha*u8, 

                Fsp == F/((alphap1)*mCore*a0),   #B.191

                #ISP
                Isp == Fsp*a0*(alphap1)/(f*g),  #B.192

                #TSFCe
                TSFCe == 1/Isp                   #B.193
                ]
        ConstraintSet.__init__(self, constraints, **kwargs)
  
class OnDesignSizing(ConstraintSet):
    """
    class to perform the on design sizing of the engine.
    Nozzle areas are calcualted in post processing due to dependence on
    M6 and M8 being greater than or less than 1

    m6opt of zero gives the constriants for M6 < 1, m6opt of 1 gives constraints
    for M6 >= 1

    m8opt of zero gives the constriants for M8 < 1, m7opt of 1 gives constraints
    for M8 >= 1
    """
    def __init__(self, m6opt, m8opt, **kwargs):
        #new variables
        a0 = Variable('a_0', 'm/s', 'Speed of Sound in Freestream')
        
        #air propeRies
        Cpair = Variable('Cp_{air}', 1003, 'J/kg/K', "Cp Value for Air at 250K")
        Cp1 = Variable('Cp_{1}', 1008, 'J/kg/K', "Cp Value for Air at 350K") #gamma = 1.398
        Cp2 = Variable('Cp_{2}', 1099, 'J/kg/K', "Cp Value for Air at 800K") #gamma = 1.354
        R = Variable('R', 287, 'J/kg/K', 'R for Air')
        Cpt =Variable('Cp_t', 1068, 'J/kg/K', "Cp Value for Combustion Products in Turbine")
        R = Variable('R_t', 287, 'J/kg/K', 'R for the Turbine Gas')
        Cptex =Variable('Cp_tex', 1029, 'J/kg/K', "Cp Value for Combustion Products at Core Exhaust") #500K, gamma = 1.387
        Cpfanex = Variable('Cp_fex', 1005, 'J/kg/K', "Cp Value for Air at 300K") #gamma =1.4
        
        #fan face variables
        hold2 = Variable('hold_{2}', '-', '1+(gamma-1)/2 * M_2**2')
        rho2 = Variable('\rho_2', 'kg/m^3', 'Air Static Density at Fan Face')
        T2 = Variable('T_2', 'K', 'Air Static Temperature at Fan Face')
        P2 = Variable('P_2', 'kPa', 'Air Static Pressure at Fan Face')
        u2 = Variable('u_2', 'm/s', 'Air Speed at Fan Face')
        A2 = Variable('A_2', 'm^2', 'Fan Area')

        #HPC face variables
        hold25 = Variable('hold_{2.5}', '-', '1+(gamma-1)/2 * M_2.5**2')
        rho25 = Variable('\rho_2.5', 'kg/m^3', 'Static Air Density at HPC Face')
        T25 = Variable('T_{2.5}', 'K', 'Static Air Temperature at HPC Face')
        P25 = Variable('P_{2.5}', 'kPa', 'Static Air Pressure at HPC Face')
        Pt25 = Variable('P_{t_2.5}', 'kPa', 'Stagnation Pressure at the LPC Exit (2.5)')
        u25 = Variable('u_{2.5}', 'm/s', 'Air Speed at HPC Face')
        A25 = Variable('A_{2.5}', 'm^2', 'HPC Area')
        Tt25 = Variable('T_{t_2.5}', 'K', 'Stagnation Temperature at the LPC Exit (2.5)')
        ht25 = Variable('h_{t_2.5}', 'J/kg', 'Stagnation Enthalpy at the LPC Exit (2.5)')
        h25 = Variable('h_{2.5}', 'J/kg', 'Static Enthalpy at the LPC Exit (2.5)')

        #mach numbers
 
        M5 = Variable('M_5', '-', 'Station 5 Mach Number')
        M7 = Variable('M_7', '-', 'Station 7 Mach Number')

        #core mass flow
        mCore = Variable('m_{core}', 'kg/s', 'Core Mass Flow')

        #variables specified for sizing purposes
        Fd = Variable('F_D', 'N', 'Design Thrust')
        M2 = Variable('M_2', '-', 'Fan Face/LPC Face Axial Mach Number')
        M25 = Variable('M_{2.5}', '-', 'HPC Face Axial Mach Number')

        #thrust variables
        Fsp = Variable('F_{sp}', '-', 'Specific Net Thrust')

        #BPR
        alphap1 = Variable('alphap1', '-', '1 plus BPR')
        alpha = Variable('alpha', '-', 'By Pass Ratio')

        Pt2 = Variable('P_{t_2}', 'kPa', 'Stagnation Pressure at the Fan Inlet (2)')
        Tt2 = Variable('T_{t_2}', 'K', 'Stagnation Temperature at the Fan Inlet (2)')
        ht2 = Variable('h_{t_2}', 'J/kg', 'Stagnation Enthalpy at the Fan Inlet (2)')
        T2 = Variable('T_{2}', 'K', 'Static Temperature at the Fan Inlet (2)')
        h2 = Variable('h_{2}', 'J/kg', 'Static Enthalpy at the Fan Inlet (2)')

        #exhaust speeds
        u6 = Variable('u_6', 'm/s', 'Core Exhaust Velocity')
        u8 = Variable('u_8', 'm/s', 'Fan Exhaust Velocity')

        #exhaust temperatures
        T6 = Variable('T_{6}', 'K', 'Core Exhaust Static Temperature (6)')
        T8 = Variable('T_{8}', 'K', 'Fan Exhaust Sttic Temperature (8)')
        T5 = Variable('T_{5}', 'K', 'Static Temperature at the Turbine Nozzle Exit (5)')
        T7 = Variable('T_{7}', 'K', 'Static Temperature at the Fan Nozzle Exit (7)')

        #exhaust static pressures to be used later
        P7 = Variable('P_{7}', 'kPa', 'Fan Exhaust Static Pressure (7)')
        P5 = Variable('P_{5}', 'kPa', 'Core Exhaust Static Pressure (5)')

        #ambient static pressure
        P0 = Variable('P_0', 'kPa', 'Free Stream Static Pressure')

        #component speeds
        #design spool speeds arbitrarily set to 1 since only ratio are considered
        NlcD = Variable('N_{lcD}', 1, '-', 'LPC Design Spool Speed')    #B.221
        NhcD =Variable('N_{hcD}', 1, '-', 'HPC Design Spool Speed') #B.222

        NbarlcD = Variable('N_{bar_lcD}', '-', 'Normalized LPC Design Spool Speed')
        NbarhcD = Variable('N_{bar_hcD}', '-', 'Normalized HPC Design Spool Speed')
        
        #design corrected mass flow
        mhtD =Variable('m_{htD}', 'kg/s', 'Design HPT Corrected Mass Flow (see B.225)')
        mltD = Variable('m_{ltD}', 'kg/s', 'Design LPT Corrected Mass Flow (see B.226)')
        mhcD = Variable('m_{hc_D}', 'kg/s', 'On Design HPC Corrected Mass Flow')

        #reference states
        Tref = Variable('T_{ref}', 'K', 'Reference Temperature for Normalization')
        Pref = Variable('P_{ref}', 'kPa', 'Reference Pressure for Normalization')

        #fuel air ratio
        f = Variable('f', '-', 'Fuel Air Mass Flow Fraction')
        
        #other states components needs to be linked to
        Pt41 = Variable('P_{t_4.1}', 'kPa', 'Stagnation Pressure at the Turbine Inlet (4.1)')
        Tt41 = Variable('T_{t_4.1}', 'K', 'Stagnation Temperature at the Turbine Inlet (4.1)')
        Pt45 = Variable('P_{t_4.5}', 'kPa', 'Stagnation Pressure at the HPT Exit (4.5)')
        Tt45 = Variable('T_{t_4.5}', 'K', 'Stagnation Temperature at the HPT Exit (4.5)')
        Tt18 = Variable('T_{t_1.8}', 'K', 'Stagnation Temperature at the Diffuser Exit (1.8)')
        Tt25 = Variable('T_{t_2.5}', 'K', 'Stagnation Temperature at the LPC Exit (2.5)')
        Tt5 = Variable('T_{t_5}', 'K', 'Stagnation Temperature at the Turbine Nozzle Exit (5)')
        Pt5 = Variable('P_{t_5}', 'kPa', 'Stagnation Pressure at the Turbine Nozzle Exit (5)')
        Pt7 = Variable('P_{t_7}', 'kPa', 'Stagnation Pressure at the Fan Nozzle Exit (7)')
        Tt7 = Variable('T_{t_7}', 'K', 'Stagnation Temperature at the Fan Nozzle Exit (7)')

        #f plus one
        fp1 = Variable('fp1', '-', 'f + 1')

        #on design normalized mass flows
        mFanBarD = Variable('m_{fan_bar_D}', 'kg/s', 'Fan On-Design Corrected Mass Flow')
        mlcD = Variable('m_{lc_D}', 'kg/s', 'On Design LPC Corrected Mass Flow')

        #fan exhuast sizing variables
        u7 = Variable('u_7', 'm/s', 'Station 7 Exhaust Velocity')
        rho7 = Variable('\rho_7', 'kg/m^3', 'Air Static Density at Fam Exhaust Exit (7)')
        A7 = Variable('A_7', 'm^2', 'Fan Exhaust Nozzle Area')

        #core exhaust sizing variables
        A5 = Variable('A_5', 'm^2', 'Core Exhaust Nozzle Area')
        u5 = Variable('u_5', 'm/s', 'Station 5 Exhaust Velocity')
        rho5 = Variable('\rho_5', 'kg/m^3', 'Air Static Density at Core Exhaust Exit (5)')

        u0 = Variable('u_0', 'm/s', 'Free Stream Speed')

        piFanD = Variable('\pi_{f_D}', '-', 'On-Design Pressure Ratio')
        pif = Variable('\pi_f', '-', 'Fan Pressure Ratio')
        pihc = Variable('\pi_{hc}', '-', 'HPC Pressure Ratio')
        pihcD = Variable('\pi_{hc_D}', '-', 'HPC On-Design Pressure Ratio')
        pilc = Variable('\pi_{lc}', '-', 'LPC Pressure Ratio')
        pilcD = Variable('\pi_{lc_D}', '-', 'LPC On-Design Pressure Ratio')

        ht4 = Variable('h_{t_4}', 'J/kg', 'Stagnation Enthalpy at the Combustor Exit (4)')
        ht3 = Variable('h_{t_3}', 'J/kg', 'Stagnation Enthalpy at the HPC Exit (3)')

        #heat of combustion of jet fuel
        hf = Variable('h_f', 42.8, 'MJ/kg', 'Heat of Combustion of Jet Fuel')     #http://hypeRbook.com/facts/2003/EvelynGofman.shtml...prob need a better source

        #engine weight
        W_engine = Variable('W_{engine}', 'N', 'Weight of a Single Turbofan Engine')

        pilc = Variable('\pi_{lc}', '-', 'LPC Pressure Ratio')
        pihc = Variable('\pi_{hc}', '-', 'HPC Pressure Ratio')

        alpha = Variable('alpha', '-', 'By Pass Ratio')
        
        with SignomialsEnabled():
            constraints = [
                #making f+1 GP compatible --> needed for convergence
                SignomialEquality(fp1,f+1),

                #mass flow sizing
                mCore == Fd/(Fsp*a0*(alphap1)),  #B.194

                #component area sizing
                #fan area
                P2 == Pt2*(hold2)**(-3.512),
                T2 == Tt2 * hold2**-1,
                h2 == Cp1 * T2,
                rho2 == P2/(R * T2),  #B.196
                u2 == M2*(Cp1*R*T2/(781*units('J/kg/K')))**.5,  #B.197
                A2 == (alphap1)*mCore/(rho2*u2),     #B.198

                #HPC area
                P25 == Pt25*(hold25)**(-3.824857),
                T25 == Tt25 * hold25**-1,
                h25 == Cp2 * T25,
                rho25 == P25/(R*T25),
                u25 == M25*(Cp2*R*T25/(781*units('J/kg/K')))**.5,   #B.202
                A25 == mCore/(rho25*u25),     #B.203

               

                #compute on design normalized turbine mass flows
                mhtD == fp1*mCore*((Tt41/Tref)**.5)/(Pt41/Pref), #B.225
                mltD == fp1*mCore*((Tt45/Tref)**.5)/(Pt45/Pref), #B.226

                #on design normalized mass flows
                mFanBarD == alpha*mCore*((Tt2/Tref)**.5)/(Pt2/Pref), #B.226
                mlcD == mCore*((Tt2/Tref)**.5)/(Pt2/Pref), #B.226
                mhcD == mCore*((Tt25/Tref)**.5)/(Pt25/Pref), #B.226

                #compute the fan exaust speed and size the nozzle
                SignomialEquality(u7**2, (2*Cpfanex*(Tt7-T7))),
                rho7 == P7/(R*T7),
                A7 == alpha*mCore/(rho7*u7),

                #compute the core exhaust speed and size the nozzle
                SignomialEquality(u5**2, (2*Cptex*(Tt5-T5))),
                rho5 == P5/(R*T5),
                A5 == mCore/(rho5*u5),

                
                #calculate the engine weight
                #using drela's original model from TASOPT source code
                TCS([W_engine >= (mCore*.0984)*(1684.5+17.7*(pilc*pihc)/30+1662.2*(alpha/5)**1.2)*units('m/s')]),
                ]
            
            if m6opt == 0:
                #if M6 is less than one add these constraints
                 constraints.extend([
                    P5 == P0,
                    T5 == Tt5*(P5/Pt5)**(.387/1.387)
                    ])
                
            if m6opt == 1:
                #if M6 is greather than or equal to 1 add these constraints
                constraints.extend([
                    M5 == 1,
                    P5 == Pt5*(1.1935)**(-3.583987),
                    T5 == Tt5*(1.1935)**-1
                    ])
                
            if m8opt == 0:
                #if M8 is less than one add these constraints
                constraints.extend([
                    P7 == P0,
                    T7 == Tt7*(P7/Pt7)**(.4/1.4)
                    ])
                
            if m8opt == 1:
                #if M8 is greather than or equal to 1 add these constraints
                constraints.extend([
                    M7 == 1,
                    P7 == Pt7*(1.2)**(-3.5),
                    T7 == Tt7*(1.2)**-1
                    ])
                
        #objective is None because all constraints are equality so feasability region is a
        #single point which likely will not solve
##        Model.__init__(self, None, constraints, **kwargs)
        ConstraintSet.__init__(self, constraints, **kwargs)
    
class LPCMap(ConstraintSet):
    """
    Implentation of TASOPT compressor map model. Map is claibrated with exponents from
    tables B.1 or B.2 of TASOPT, making the maps realistic for the E3 compressor.
    Map is used for off-design calculations.
    Variables link with off design LPC variables.
    """
    def __init__(self, **kwargs):
        #Temperature Variables
        Tt2 = Variable('T_{t_2}', 'K', 'Stagnation Temperature at the Fan Inlet (2)')
        Tref = Variable('T_{ref}', 'K', 'Reference Stagnation Temperature')

        #Mass Flow Variables
        mlc = Variable('m_{lc}', 'kg/s', 'LPC Corrected Mass Flow')
        mCore = Variable('m_{core}', 'kg/s', 'Core Mass Flow')
        mtildlc = Variable('m_{tild_lc}', '-', 'LPC Normalized Mass Flow')
        mlcD = Variable('m_{lc_D}', 'kg/s', 'On Design LPC Corrected Mass Flow')

        #Pressure Variables
        Pt2 = Variable('P_{t_2}', 'kPa', 'Stagnation Pressure at the Fan Inlet (2)')
        Pref = Variable('P_{ref}', 'kPa', 'Reference Stagnation Pressure')

        #pressure ratio variables
        ptildlc = Variable('p_{tild_lc}', '-', 'LPC Normalized Pressure Ratio')
        pilc = Variable('\pi_{lc}', '-', 'LPC Pressure Ratio')
        pilcD = Variable('\pi_{lc_D}', '-', 'LPC On-Design Pressure Ratio')
        
        #Speed Variables...by setting the design speed to be 1 since only ratios are
        #impoRant I was able to drop out all the other speeds
        N1 = Variable('N_1', '-', 'LPC Speed')

        #Spine Paramterization Variables
        mtildslc = Variable('m_{{tild}_slc}', '-', 'LPC Spine Parameterization Variable')
        ptildslc = Variable('p_{{tild}_slc}', '-', 'LPC Spine Parameterization Variable')

        with SignomialsEnabled():
            constraints = [
                #define mbar..technially not needed b/c constrained in res 2 and/or 3
                TCS([mlc == mCore*((Tt2/Tref)**.5)/(Pt2/Pref)]),    #B.280

                #define mtild
                mtildlc == mlc/mlcD,   #B.282

                #define ptild
                #SIGNOMIAL
                SignomialEquality(ptildlc * (pilcD-1), (pilc-1)),    #B.281
                
                #constrain the "knee" shape of the map, monomial is from gpfit
                ptildlc == ((N1**.28)*(mtildlc**-.00011))**10,
                ]
                
##            Model.__init__(self, 1/pilc, constraints, **kwargs)
            ConstraintSet.__init__(self, constraints, **kwargs)
        

class HPCMap(ConstraintSet):
    """
    Implentation of TASOPT compressor map model. Map is claibrated with exponents from
    tables B.1 or B.2 of TASOPT, making the maps realistic for the E3 compressor.
    Map is used for off-design calculations.
    Variables link with off design HPC variables.
    """
    def __init__(self, **kwargs):
        #Temperature Variables
        Tt25 = Variable('T_{t_2.5}', 'K', 'Stagnation Temperature at the LPC Exit (2.5)')
        Tref = Variable('T_{ref}', 'K', 'Reference Stagnation Temperature')

        #Mass Flow Variables
        mhc = Variable('m_{lc}', 'kg/s', 'HPC Corrected Mass Flow')
        mCore = Variable('m_{core}', 'kg/s', 'Core Mass Flow')
        mtildhc = Variable('m_{tild_hc}', '-', 'HPC Normalized Mass Flow')
        mhcD = Variable('m_{hc_D}', 'kg/s', 'On Design HPC Corrected Mass Flow')

        #Pressure Variables
        Pt25 = Variable('P_{t_2.5}', 'kPa', 'Stagnation Pressure at the LPC Exit (2.5)')
        Pref = Variable('P_{ref}', 'kPa', 'Reference Stagnation Pressure')

        #pressure ratio variables
        ptildhc = Variable('p_{tild_lc}', '-', 'LPC Normalized Pressure Ratio')
        pihc = Variable('\pi_{hc}', '-', 'HPC Pressure Ratio')
        pihcD = Variable('\pi_{hc_D}', '-', 'HPC On-Design Pressure Ratio')
        
        #Speed Variables...by setting the design speed to be 1 since only ratios are
        #impoRant I was able to drop out all the other speeds
        N2 = Variable('N_2', '-', 'HPC Speed')

        #Spine Paramterization Variables
        mtildshc = Variable('m_{{tild}_shc}', '-', 'HPC Spine Parameterization Variable')
        ptildshc = Variable('p_{{tild}_shc}', '-', 'HPC Spine Parameterization Variable')

        with SignomialsEnabled():
            constraints = [
                #define mtild
                mtildhc == mhc/mhcD,   #B.282

                #define ptild
                #SIGNOMIAL
                SignomialEquality(ptildhc * (pihcD-1), (pihc-1)),    #B.281
               
                #constrain the "knee" shape of the map, monomial is from gpfit
                ptildhc == ((N2**.28)*(mtildhc**-.00011))**10,
                ]
                
##            Model.__init__(self, 1/pihc, constraints, **kwargs)
            ConstraintSet.__init__(self, constraints, **kwargs)

class FanMap(ConstraintSet):
    """
    Implentation of TASOPT compressor map model. Map is claibrated with exponents from
    tables B.1 or B.2 of TASOPT, making the map realistic for the E3 fan.
    Map is used for off-design calculations, links with fan variables.
    """
    def __init__(self, **kwargs):
        #Temperature Variables
        Tt2 = Variable('T_{t_2}', 'K', 'Stagnation Temperature at the Fan Inlet (2)')
        Tref = Variable('T_{ref}', 'K', 'Reference Stagnation Temperature')

        #Mass Flow Variables
        mf = Variable('m_{f}', 'kg/s', 'Fan Corrected Mass Flow')
        mFan = Variable('m_{fan}', 'kg/s', 'Fan Mass Flow')
        mtildf = Variable('m_{tild_f}', '-', 'Fan Normalized Mass Flow')
        mFanD = Variable('m_{fan_D}', 'kg/s', 'Fan On-Design Mass Flow')
        mFanBarD = Variable('m_{fan_bar_D}', 'kg/s', 'Fan On-Design Corrected Mass Flow')


        #Pressure Variables
        Pt2 = Variable('P_{t_2}', 'kPa', 'Stagnation Pressure at the Fan Inlet (2)')
        Pref = Variable('P_{ref}', 'kPa', 'Reference Stagnation Pressure')

        #pressure ratio variables
        ptildf = Variable('p_{tildf}', '-', 'Fan Normalized Pressure Ratio')
        pif = Variable('\pi_f', '-', 'Fan Pressure Ratio')
        piFanD = Variable('\pi_{f_D}', '-', 'On-Design Pressure Ratio')
        
        #Speed Variables...by setting the design speed to be 1 since only ratios are
        #impoRant I was able to drop out all the other speeds
        Nf = Variable('N_f', '-', 'Fan Speed')
        
        #Spine Paramterization Variables
        mtildsf = Variable('m_{{tild}_sf}', '-', 'Fan Spine Parameterization Variable')
        ptildsf = Variable('p_{{tild}_sf}', '-', 'Fan Spine Parameterization Variable')

        with SignomialsEnabled():
            constraints = [
                #define mbar
                mf == mFan*((Tt2/Tref)**.5)/(Pt2/Pref),    #B.280

                #define mtild
                mtildf == mf/mFanBarD,   #B.282

                #define ptild
                #SIGNOMIAL
                SignomialEquality(ptildf * (piFanD-1), (pif-1)),    #B.281

                #constrain the "knee" shape of the map, monomial is from gpfit
                ptildf == ((Nf**.28)*(mtildf**-.00011))**10,
                ]
              
##            Model.__init__(self, 1/pif, constraints, **kwargs)
            ConstraintSet.__init__(self, constraints, **kwargs)
        

class OffDesign(ConstraintSet):
    """
    Class to implement off design performance of a turbofan. Simply equates the residuals
    from section B.6 of TASOPT. The constraints inside this model should be linked with the
    constraints in the compressor map model, as well as within the individual component models.
    Note that a turbine map is not needed, instead the turbine is assumed to be choked.
    Inputs: res7 value of 1 --> residual 7 is the Tt4 constraint
    res7 value of 0 --> residual 7 is the thrust constraint
    m5opt of zero gives the constriants for M5 < 1, m5opt of 1 gives constraints
    for M5 >= 1
    m7opt of zero gives the constriants for M7 < 1, m7opt of 1 gives constraints
    for M7 >= 1
    """
    def __init__(self, res7, m5opt, m7opt, **kwargs):
        #define all the variables
        #gas propeRies
        R = Variable('R', 287, 'J/kg/K', 'R')
        Cpair = Variable('Cp_{air}', 1068, 'J/kg/K', "Cp Value for Air at 673K") #http://www.engineeringtoolbox.com/air-propeRies-d_156.html
        Cptex =Variable('Cp_tex', 1029, 'J/kg/K', "Cp Value for Combustion Products at Core Exhaust") #500K, gamma = 1.387
        Cpfanex = Variable('Cp_fex', 1005, 'J/kg/K', "Cp Value for Air at 300K") #gamma =1.4
        
        #free stream static pressure
        P0 = Variable('P_0', 'kPa', 'Free Stream Static Pressure')
        
        #speeds
        Nf = Variable('N_f', '-', 'Fan Speed')
        N1 = Variable('N_1', '-', 'LPC Speed')

        NlcD = Variable('N_{lcD}', 1, '-', 'LPC Design Spool Speed')    #B.221
        NhcD =Variable('N_{hcD}', 1, '-', 'HPC Design Spool Speed') #B.222
        
        #design normalized component speeds
        NbarlcD = Variable('N_{barlc_D}', '-', 'Normalized LPC Design Speed')
        NbarhcD = Variable('N_{barhc_D}', '-', 'Normalized HPC Design Speed')

        #gear ratio, set to 1 if no gearing present
        Gf = Variable('G_f', '', 'Gear Ratio Between Fan and LPC')

        #fuel air ratio
        f = Variable('f', '-', 'Fuel Air Mass Flow Fraction')

        #diffuser exit states
        Pt18 = Variable('P_{t_1.8}', 'kPa', 'Stagnation Pressure at the Diffuser Exit (1.8)')
        Tt18 = Variable('T_{t_1.8}', 'K', 'Stagnation Temperature at the Diffuser Exit (1.8)')
        ht18 = Variable('h_{t_1.8}', 'J/kg', 'Stagnation Enthalpy at the Diffuser Exit (1.8)')

        #fan inlet states
        Pt2 = Variable('P_{t_2}', 'kPa', 'Stagnation Pressure at the Fan Inlet (2)')
        Tt2 = Variable('T_{t_2}', 'K', 'Stagnation Temperature at the Fan Inlet (2)')

        #turbine inlet states
        Pt41 = Variable('P_{t_4.1}', 'kPa', 'Stagnation Pressure at the Turbine Inlet (4.1)')
        Tt41 = Variable('T_{t_4.1}', 'K', 'Stagnation Temperature at the Turbine Inlet (4.1)')

        #LPC exit states
        Pt25 = Variable('P_{t_2.5}', 'kPa', 'Stagnation Pressure at the LPC Exit (2.5)')
        Tt25 = Variable('T_{t_2.5}', 'K', 'Stagnation Temperature at the LPC Exit (2.5)')

        #Corrected mass flows
        mf = Variable('m_{f}', 'kg/s', 'Fan Corrected Mass Flow')
        mlc = Variable('m_{lc}', 'kg/s', 'LPC Corrected Mass Flow')
        mhc =  Variable('m_{hc}', 'kg/s', 'HPC Corrected Mass Flow')
        mhtD = Variable('m_{htD}', 'kg/s', 'Design HPT Corrected Mass Flow (see B.225)')
        mltD = Variable('m_{ltD}', 'kg/s', 'Design LPT Corrected Mass Flow (see B.226)')

        #HPT exit states
        Pt45 = Variable('P_{t_4.5}', 'kPa', 'Stagnation Pressure at the HPT Exit (4.5)')
        Tt45 = Variable('T_{t_4.5}', 'K', 'Stagnation Temperature at the HPT Exit (4.5)')

        #fan exhuast states
        P7 = Variable('P_{7}', 'kPa', 'Fan Exhaust Static Pressure (7)')
        T7 = Variable('T_{7}', 'K', 'Static Temperature at the Fan Nozzle Exit (7)')
        u7 = Variable('u_7', 'm/s', 'Station 7 Exhaust Velocity')
        M7 = Variable('M_7', '-', 'Station 7 Mach Number')
        rho7 = Variable('\rho_7', 'kg/m^3', 'Air Static Density at Fam Exhaust Exit (7)')
        Pt7 = Variable('P_{t_7}', 'kPa', 'Stagnation Pressure at the Fan Nozzle Exit (7)')
        Tt7 = Variable('T_{t_7}', 'K', 'Stagnation Temperature at the Fan Nozzle Exit (7)')

        #core exhaust states
        P5 = Variable('P_{5}', 'kPa', 'Core Exhaust Static Pressure (5)')
        T5 = Variable('T_{5}', 'K', 'Static Temperature at the Turbine Nozzle Exit (5)')
        M5 = Variable('M_5', '-', 'Station 5 Mach Number')
        u5 = Variable('u_5', 'm/s', 'Station 5 Exhaust Velocity')
        rho5 = Variable('\rho_5', 'kg/m^3', 'Air Static Density at Core Exhaust Exit (5)')
        Pt5 = Variable('P_{t_5}', 'kPa', 'Stagnation Pressure at the Turbine Nozzle Exit (5)')
        Tt5 = Variable('T_{t_5}', 'K', 'Stagnation Temperature at the Turbine Nozzle Exit (5)')

        #nozzle areas
        #these values needs to be subbed in from the post computation on the on design case
        A5 = Variable('A_5', 'm^2', 'Core Exhaust Nozzle Area')
        A7 = Variable('A_7', 'm^2', 'Fan Exhaust Nozzle Area')

        #burner exit temperatures (station 4)
        Tt4 = Variable('T_{t_4}', 'K', 'Combustor Exit (Station 4) Stagnation Temperature')
        Tt4spec = Variable('T_{t_{4spec}}', 'K', 'Specified Combustor Exit (Station 4) Stagnation Temperature')

        #pressure ratios
        pitn = Variable('\pi_{tn}', '-', 'Turbine Nozzle Pressure Ratio')
        
        #HPT exit states
        Pt49 = Variable('P_{t_4.9}', 'kPa', 'Stagnation Pressure at the HPTExit (4.9)')
        Tt49 = Variable('T_{t_4.9}', 'K', 'Stagnation Temperature at the HPT Exit (4.9)')

        #reference states
        Tref = Variable('T_{ref}', 'K', 'Reference Temperature for Normalization')
        Pref = Variable('P_{ref}', 'kPa', 'Reference Pressure for Normalization')

        #define the f plus one variable, limits the number of signomials
        fp1 = Variable('fp1', '-', 'f + 1')

        #core mass flow
        mCore = Variable('m_{core}', 'kg/s', 'Core Mass Flow')
        mFan = Variable('m_{fan}', 'kg/s', 'Fan Mass Flow')
        
        #variables for the thrust constraint
        Fspec = Variable('F_{spec}', 'N', 'Specified Total Thrust')
        F = Variable('F', 'N', 'Total Thrust')

        #exit velocities
        u0 = Variable('u_0', 'm/s', 'Free Stream Speed')
        u6 = Variable('u_6', 'm/s', 'Core Exhaust Velocity')
        u8 = Variable('u_8', 'm/s', 'Fan Exhaust Velocity')

        pihc = Variable('\pi_{hc}', '-', 'HPC Pressure Ratio')

        ht4 = Variable('h_{t_4}', 'J/kg', 'Stagnation Enthalpy at the Combustor Exit (4)')
        ht3 = Variable('h_{t_3}', 'J/kg', 'Stagnation Enthalpy at the HPC Exit (3)')
    
        #heat of combustion of jet fuel
        hf = Variable('h_f', 42.8, 'MJ/kg', 'Heat of Combustion of Jet Fuel')     #http://hypeRbook.com/facts/2003/EvelynGofman.shtml...prob need a better source

        a5 = Variable('a_5', 'm/s', 'Speed of Sound at Station 5')
        a7 = Variable('a_7', 'm/s', 'Speed of Sound at Station 7')
        with SignomialsEnabled():
            constraints = [
                #making f+1 GP compatible --> needed for convergence
                SignomialEquality(fp1,f+1),
                
                #residual 1 Fan/LPC speed
                Nf*Gf == N1,
                #loose constraints on speed needed to prevent N from sliding out
                #to zero or infinity
                N1 >= .1,
                N1 <= 2,

                #note residuals 2 and 3 differ from TASOPT, by replacing mhc with mlc
                #in residual 4 I was able to remove the LPC/HPC mass flow equality
                #in residual 6 which allows for convergence
                #residual 2 HPT mass flow
                TCS([mhtD == (fp1)*mhc*(Pt25/Pt41)*(Tt41/Tt25)**.5]),
                
                #residual 3 LPT mass flow
                TCS([(fp1)*mlc*(Pt18/Pt45)*(Tt45/Tt18)**.5 == mltD]),
                
                #residual 4
##                SignomialEquality(u7**2 +2*Cpfanex*T7, 2*Cpfanex*Tt7),
                a7 == (1.4*R*T7)**.5,
                a7*M7==u7,
                rho7 == P7/(R*T7),
                TCS([mf*(Pt2/Pref)*(Tref/Tt2)**.5 == rho7*A7*u7]),
                
                #residual 5 core nozzle mass flow
##                SignomialEquality(u5**2 +2*Cptex*T5, 2*Cptex*Tt5),
                a5 == (1.387*R*T5)**.5,
                a5*M5 == u5,
                rho5 == P5/(R*T5),
                
                #compute core mass flux
                mCore == rho5 * A5 * u5/(fp1),

                #compute fan mas flow
                mFan == rho7*A7*u7,
                
                #residual 6 LPC/HPC mass flow constraint
                TCS([mlc*(Pt18/Pref)*(Tref/Tt18)**.5 == mCore]),
                
                #residual 8, constrain the core exit total pressure
                Pt49*pitn == Pt5, #B.269

                #constrain the exit exhaust exit speeds
##                u5 >= u0,
##                u7 >= u0,
                ]
                
            if res7 == 0:
                constraints.extend([
                    #residual 7
                    #option #1, constrain the engine's thrust
                    F == Fspec,
                    Tt4 <= 2500*units('K'),
                    Tt4 >= 500*units('K'),
                    ])
            
            if res7 == 1:
                constraints.extend([
                    #residual 7
                    #option #2 constrain the burner exit temperature
                    Tt4 == Tt4spec,  #B.265
                    ])
                
            if m5opt == 0:
                 constraints.extend([
##                    P5 == P0,
##                    (P5/Pt5) == (T5/Tt5)**(3.583979),
##                    M5 == u5/((T5*Cptex*R/(781*units('J/kg/K')))**.5),

                    P5 >= P0,
                    (P5/Pt5) == (T5/Tt5)**(3.583979),
##                    M7 == u7/((T7*Cpfanex*R/(781*units('J/kg/K')))**.5),
                    (T5/Tt5)**-1 >= 1 + .2 * M5**2,
                    M5 <= 1,
                    ])
                 
            if m5opt == 1:
                 constraints.extend([
##                    M5 == 1,
##                    P5 == Pt5*(1.1935)**(-3.583979),
##                    T5 == Tt5*1.1935**(-1)

                    P5 >= P0,
                    (P5/Pt5) == (T5/Tt5)**(3.583979),
##                    M7 == u7/((T7*Cpfanex*R/(781*units('J/kg/K')))**.5),
                    (T5/Tt5)**-1 >= 1 + .2 * M5**2,
                    M5 <= 1,
                    ])
                 
            if m7opt == 0:
                constraints.extend([
                    #additional constraints on residual 4 for M7 < 1
##                    P7 == P0,
##                    (P7/Pt7) == (T7/Tt7)**(3.5),
##                    M7 == u7/((T7*Cpfanex*R/(781*units('J/kg/K')))**.5),

                    P7 >= P0,
                    (P7/Pt7) == (T7/Tt7)**(3.5),
##                    M7 == u7/((T7*Cpfanex*R/(781*units('J/kg/K')))**.5),
                    (T7/Tt7)**-1 >= 1 + .2 * M7**2,
##                    SignomialEquality((T7/Tt7)**-1, 1 + .2 * M7**2),
                    M7 <= 1,
##                    M7>=0.5
                    u7>=u0
                    ])
                
            if m7opt == 1:
                 constraints.extend([
                     #additional constraints on residual 4 for M7 >= 1
##                     M7 == 1,
##                     P7 == Pt7*(1.2)**(-1.4/.4),
##                     T7 == Tt7*1.2**(-1)

                    P7 >= P0,
                    (P7/Pt7) == (T7/Tt7)**(3.5),
##                    M7 == u7/((T7*Cpfanex*R/(781*units('J/kg/K')))**.5),
##                    SignomialEquality((T7/Tt7)**-1, 1 + .2 * M7**2),
                    (T7/Tt7)**-1 >= 1 + .2 * M7**2,
                    M7 <= 1,
                    u7>=u0
                    ])
                 
##        Model.__init__(self, 1/u7, constraints, **kwargs)
        ConstraintSet.__init__(self, constraints, **kwargs)


        

