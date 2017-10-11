" empennage.py "
from gpkit import Variable, Model
from .horizontal_tail import HorizontalTail
from .vertical_tail import VerticalTail
from .tail_boom import TailBoom, TailBoomState

#pylint: disable=attribute-defined-outside-init
class Empennage(Model):
    "empennage model, consisting of vertical, horizontal and tailboom"
    def setup(self):
        mfac = Variable("m_{fac}", 1.0, "-", "Tail weight margin factor")
        W = Variable("W", "lbf", "empennage weight")

        self.horizontaltail = HorizontalTail()
        self.verticaltail = VerticalTail()
        self.tailboom = TailBoom()
        self.components = [self.horizontaltail, self.verticaltail,
                           self.tailboom]

        state = TailBoomState()
        loading = [self.tailboom.horizontalbending(self.horizontaltail, state),
                   self.tailboom.verticalbending(self.verticaltail, state),
                   self.tailboom.verticaltorsion(self.verticaltail, state)]

        constraints = [
            W/mfac >= (self.horizontaltail["W"] + self.verticaltail["W"]
                       + self.tailboom["W"]),
            self.tailboom["l"] >= self.horizontaltail["l_h"],
            self.tailboom["l"] >= self.verticaltail["l_v"],
            ]

        return self.components, constraints, loading
