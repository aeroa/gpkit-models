" test tail models "
from gpkitmodels.GP.aircraft.tail.horizontal_tail import HorizontalTail
from gpkitmodels.GP.aircraft.tail.vertical_tail import VerticalTail
from gpkitmodels.GP.aircraft.tail.empennage import Empennage
from gpkitmodels.GP.aircraft.wing.wing_test import FlightState
from gpkitmodels.GP.aircraft.wing.boxspar import BoxSpar
from gpkit import Model, Variable, units

#pylint: disable=no-member

def test_htail():

    Sw = Variable("S_w", 50, "ft**2", "wing area")
    cmac = Variable("cmac", 15, "in", "wing MAC")
    ht = HorizontalTail()
    fs = FlightState()
    ht.substitutions.update({ht.W: 5, ht.mh: 0.01, ht.planform.AR: 4,
                             ht.Vh: 0.5, ht.lh: 10})
    perf = ht.flight_model(ht, fs)

    m = Model(perf.Cd, [ht.Vh <= ht.planform.S*ht.lh/Sw/cmac, ht, perf])
    m.solve(verbosity=0)

def test_vtail():

    Sw = Variable("S_w", 50, "ft**2", "wing area")
    bw = Variable("b_w", 20, "ft", "wing span")
    vt = VerticalTail()
    fs = FlightState()
    vt.substitutions.update({vt.W: 5, vt.planform.AR: 3, vt.Vv: 0.04,
                             vt.lv: 10})
    perf = vt.flight_model(vt, fs)

    m = Model(perf.Cd, [vt.Vv <= vt.planform.S*vt.lv/Sw/bw, vt, perf])
    m.solve(verbosity=0)

def test_emp():

    Sw = Variable("S_w", 50, "ft**2", "wing area")
    bw = Variable("b_w", 20, "ft", "wing span")
    cmac = Variable("cmac", 15, "in", "wing MAC")
    emp = Empennage()
    fs = FlightState()
    emp.substitutions.update({emp.W: 10, emp.tailboom.l: 5,
                              emp.htail.planform.AR: 4,
                              emp.vtail.planform.AR: 4,
                              emp.vtail.Vv: 0.04,
                              emp.htail.Vh: 0.4,
                              emp.htail.mh: 0.01})
    htperf = emp.htail.flight_model(emp.htail, fs)
    vtperf = emp.vtail.flight_model(emp.vtail, fs)
    tbperf = emp.tailboom.flight_model(emp.tailboom, fs)

    from gpkit import settings
    if settings["default_solver"] == "cvxopt":
        for l in [emp.hbend, emp.vbend]:
            for v in ["\\bar{M}_{tip}", "\\bar{\\delta}_{root}",
                      "\\theta_{root}"]:
                l.substitutions[v] = 1e-3

    m = Model(htperf.Cd + vtperf.Cd + tbperf.Cf,
              [emp.vtail.lv == emp.tailboom.l, emp.htail.lh == emp.tailboom.l,
               emp.htail.Vh <= emp.htail.planform.S*emp.htail.lh/Sw/cmac,
               emp.vtail.Vv <= emp.vtail.planform.S*emp.vtail.lv/Sw/bw,
               emp, fs, htperf, vtperf, tbperf])
    m.solve(verbosity=0)

def test_tailboom_mod():

    Sw = Variable("S_w", 50, "ft**2", "wing area")
    bw = Variable("b_w", 20, "ft", "wing span")
    cmac = Variable("cmac", 15, "in", "wing MAC")
    cmax = Variable("cmax", 5, "in", "max width")
    emp = Empennage(N=5, tailboomSpar=BoxSpar)
    fs = FlightState()
    emp.substitutions.update({emp.W: 10, emp.tailboom.l: 5,
                              emp.htail.planform.AR: 4,
                              emp.vtail.planform.AR: 4,
                              emp.vtail.Vv: 0.04,
                              emp.htail.Vh: 0.4,
                              emp.htail.mh: 0.01,
                              emp.tailboom.wlim: 1})
    htperf = emp.htail.flight_model(emp.htail, fs)
    vtperf = emp.vtail.flight_model(emp.vtail, fs)
    tbperf = emp.tailboom.flight_model(emp.tailboom, fs)

    from gpkit import settings
    if settings["default_solver"] == "cvxopt":
        for l in [emp.hbend, emp.vbend]:
            for v in ["\\bar{M}_{tip}", "\\bar{\\delta}_{root}",
                      "\\theta_{root}"]:
                l.substitutions[v] = 1e-3

    m = Model(htperf.Cd + vtperf.Cd + tbperf.Cf,
              [emp.vtail.lv == emp.tailboom.l, emp.htail.lh == emp.tailboom.l,
               emp.htail.Vh <= emp.htail.planform.S*emp.htail.lh/Sw/cmac,
               emp.vtail.Vv <= emp.vtail.planform.S*emp.vtail.lv/Sw/bw,
               emp.tailboom.cave <= cmax,
               emp, fs, htperf, vtperf, tbperf])
    m.solve(verbosity=0)

def test():
    test_htail()
    test_vtail()
    test_emp()
    test_tailboom_mod()

if __name__ == "__main__":
    test()
