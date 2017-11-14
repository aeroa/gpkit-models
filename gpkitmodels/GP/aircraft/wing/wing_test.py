" wing test "
from gpkitmodels.GP.aircraft.wing.wing import Wing
from gpkit import Variable, Model

#pylint: disable=no-member

class FlightState(Model):
    " state variables "
    def setup(self):

        V = Variable("V", 50, "m/s", "airspeed")
        rho = Variable("\\rho", 1.255, "kg/m^3", "air density")
        mu = Variable("\\mu", 1.5e-5, "N*s/m**2", "air viscosity")

        constraints = [V == V, rho == rho, mu == mu]

        return constraints

def test():
    " test wing models "

    W = Wing()
    W.substitutions[W.topvar("W")] = 50
    fs = FlightState()
    perf = W.flight_model(W, fs)
    loading = [W.spar.loading(W)]
    loading[0].substitutions["W"] = 100
    loading.append(W.spar.gustloading(W))
    loading[1].substitutions["W"] = 100

    m = Model(perf.Cd, [
        loading[1]["V"] == fs["V"],
        loading[1]["c_l"] == perf.CL,
        loading[1]["W_w"] == W.topvar("W"),
        loading[1]["W_w"] <= 0.5*fs["\\rho"]*fs["V"]**2*perf.CL*W.planform.S,
        W, fs, perf, loading])
    m.solve(verbosity=0)

if __name__ == "__main__":
    test()
