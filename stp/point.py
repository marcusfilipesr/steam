from . import Q_
from .state import State


class Point:
    def __init__(
        self,
        inlet=None,
        disch=None,
        disch_p=None,
        speed=None,
        eff=None,
        power=None,
        flow_v=None,
        flow_m=None,
    ) -> None:
        self.inlet = inlet
        self.disch = disch
        self.disch_p = disch_p
        self.speed = speed
        self.eff = eff
        self.power = power
        self.flow_m = flow_m
        self.flow_v = flow_v

        self.discharge = self._calc_discharge()

    def _calc_discharge(self):
        h_i = self.inlet.enthalpy()
        s_i = self.inlet.entropy()

        # isentropic discharge
        disch_isentropic = State(p=self.disch_p, s=s_i)
        if self.eff is None:
            return disch_isentropic
        else:
            h_d = h_i - (h_i - disch_isentropic.enthalpy()) * self.eff
            disch = State(p=self.disch_p, h=h_d)

        return disch
    
    def enthalpy_coefficient(self, speed):

        if speed is None:
            N = 1
        else:
            N = speed
            
        delta_h = self.discharge.enthalpy() - self.inlet.enthalpy()

        return Q_(delta_h / (N ** 2), "dimensionless")