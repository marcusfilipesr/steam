import numpy as np
from scipy.optimize import newton

from . import Q_
from .state import State


class Point:
    def __init__(
        self,
        inlet=None,
        disch=None,
        disch_p=None,
        disch_x=None,
        speed=None,
        eff=None,
        power=None,
        flow_v=None,
        flow_m=None,
        volume_ratio=None,
        phi=None,
    ) -> None:
        self.inlet = inlet
        self.disch = disch
        self.disch_p = disch_p
        self.disch_x = disch_x
        self.speed = speed
        self.eff = eff
        self.power = power
        self.flow_m = flow_m
        self.flow_v = flow_v
        self.volume_ratio = volume_ratio
        self.phi = phi

        kwargs_list = []
        kwargs_dict = {}

        for k in [
            "inlet",
            "disch",
            "disch_p",
            "disch_x",
            "speed",
            "eff",
            "power",
            "flow_v",
            "flow_m",
            "volume_ratio",
            "phi",
        ]:
            if getattr(self, k) is not None:
                kwargs_list.append(k)
                kwargs_dict[k] = getattr(self, k)

        kwargs_str = "_".join(sorted(kwargs_list))

        if self.speed is None:
            self.speed_unit = "percent"
            self.speed = Q_(100, self.speed_unit)
        else:
            self.speed_unit = self.speed.u

        try:
            getattr(self, "_calc_from_" + kwargs_str)()
        except AttributeError:
            func_str = "_calc_from_" + kwargs_str
            missed_params = []
            for k in dir(self):
                if func_str in k:
                    missed_params.append(k.replace(func_str, "").replace("_", ""))

            raise Exception(
                f"One of the following parameters was not passed to the class:\n    {missed_params}"
            )

        self.enthalpy_coeff = self.enthalpy_coefficient()
        self.phi = self.calc_phi_inlet(self.speed)
        self.phi_disch = self.calc_phi_disch()
        self.steam_rate = self.calc_steam_rate()

        # for k in ["inlet", "disch"]:
        #     setattr(self, f"phi_{k}", getattr(self,"calc_phi_" + k)())

    def _calc_from_disch_p_eff_flow_m_inlet_phi(self):
        h_i = self.inlet.enthalpy()
        s_i = self.inlet.entropy()
        # isentropic discharge
        disch_isentropic = State(p=self.disch_p, s=s_i)
        h_d = h_i - (h_i - disch_isentropic.enthalpy()) * self.eff

        self.disch = State(p=self.disch_p, h=h_d)
        self.power = np.abs(h_d - h_i) * self.flow_m
        self.flow_v = self.flow_m * self.inlet.volume()
        self.volume_ratio = self.disch.volume() / self.inlet.volume()

        def calc_speed(x):
            new_phi = self.calc_phi_inlet(x)
            return self.phi.m - new_phi.m

        speed = newton(calc_speed, (self.speed.m) * 0.1)
        self.speed = Q_(speed, self.speed_unit)

    def _calc_from_disch_p_eff_flow_m_inlet_speed(self):
        h_i = self.inlet.enthalpy()
        s_i = self.inlet.entropy()
        # isentropic discharge
        disch_isentropic = State(p=self.disch_p, s=s_i)
        h_d = h_i - (h_i - disch_isentropic.enthalpy()) * self.eff

        self.disch = State(p=self.disch_p, h=h_d)
        self.power = np.abs(h_d - h_i) * self.flow_m
        self.flow_v = self.flow_m * self.inlet.volume()
        self.volume_ratio = self.disch.volume() / self.inlet.volume()

    def _calc_from_disch_p_disch_x_flow_m_inlet(self):
        h_i = self.inlet.enthalpy()
        s_i = self.inlet.entropy()
        # isentropic discharge
        disch_isentropic = State(p=self.disch_p, s=s_i)

        self.disch = State(p=self.disch_p, x=self.disch_x)
        self.power = np.abs(
            self.disch.enthalpy() - self.inlet.enthalpy()
        ) * self.flow_m.to("kg/s")
        self.flow_v = self.flow_m * self.inlet.volume()
        self.eff = (h_i - self.disch.enthalpy()) / (h_i - disch_isentropic.enthalpy())
        self.volume_ratio = self.disch.volume() / self.inlet.volume()

    def enthalpy_coefficient(self):
        delta_h = np.abs(self.disch.enthalpy() - self.inlet.enthalpy())
        return Q_(delta_h.m / (self.speed.m**2), "dimensionless")

    def calc_phi_inlet(self, speed):
        phi = self.flow_v.to("(m ** 3)/s") / speed
        return Q_(phi.m, "dimensionless")

    def calc_phi_disch(self):
        phi = (self.flow_m * self.disch.volume()).to("(m ** 3)/s") / self.speed
        return Q_(phi.m, "dimensionless")

    def calc_steam_rate(self):
        SR = self.flow_m.to("kg/h") / self.power.to("kW")
        return SR
