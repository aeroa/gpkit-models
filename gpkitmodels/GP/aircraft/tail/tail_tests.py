" test tail models "
from gpkitmodels.GP.aircraft.tail.horizontal_tail import HorizontalTail
from gpkitmodels.GP.aircraft.tail.vertical_tail import VerticalTail
from gpkitmodels.GP.aircraft.tail.empennage import Empennage
from gpkitmodels.GP.aircraft.wing.wing_test import FlightState
from gpkit import Model

def test_htail():

    ht = HorizontalTail()
    fs = FlightState()
    ht.substitutions.update({ht.topvar("W"): 5, "m_h": 0.01, "AR": 4})
    perf = ht.flight_model(ht, fs)

    m = Model(perf["C_d"], [ht, perf])
    m.solve(verbosity=0)

def test_vtail():

    ht = VerticalTail()
    fs = FlightState()
    ht.substitutions.update({ht.topvar("W"): 5, "AR": 3})
    perf = ht.flight_model(ht, fs)

    m = Model(perf["C_d"], [ht, perf])
    m.solve(verbosity=0)

# def test_emp():
#
#     emp = Empennage()
#     fs = FlightState()
#     emp.substitutions.update({emp.topvar("W"): 10, "l": 5,
#                               emp.htail.planform["AR"]: 4,
#                               emp.vtail.planform["AR"]: 4})
#     htperf = emp.htail.flight_model(emp.htail, fs)
#     vtperf = emp.vtail.flight_model(emp.vtail, fs)
#     tbperf = emp.tailboom.flight_model(fs)
#
#     m = Model(htperf["C_d"] + vtperf["C_d"] + tbperf["C_f"],
#               [emp, fs, htperf, vtperf, tbperf])
#     m.solve(verbosity=0)

def test():
    test_htail()
    test_vtail()
    # test_emp()

if __name__ == "__main__":
    test()
