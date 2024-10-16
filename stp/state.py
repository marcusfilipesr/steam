from copy import copy
from iapws import IAPWS97

from . import Q_
from .config.units import check_units


class State(IAPWS97):
    @check_units
    def __init__(self, p=None, T=None, h=None, s=None, x=None) -> None:
        self.init_args = dict(p=p, T=T, h=h, s=s, x=x)
        self.setup_args = copy(self.init_args)

        self.update(**self.setup_args)

    def pressure(self, units=None):
        p = Q_(self.P, "MPa")
        if units:
            p = p.to(units)
        return p

    def temperature(self, units=None):
        T = Q_(self.T, "kelvin")
        if units:
            T = T.to(units)
        return T

    def enthalpy(self, units=None):
        h = Q_(self.h, "kJ/kg")
        if units:
            h = h.to(units)
        return h

    def entropy(self, units=None):
        s = Q_(self.s, "kJ/(kg * degK)")
        if units:
            s = s.to(units)
        return s
    
    def volume(self, units=None):
        v = Q_(self.v, "(m ** 3) / kg")
        if units:
            v = v.to(units)
        return v
    
    def density(self, units=None):
        rho = Q_(self.rho, "kg/(m ** 3)")
        if units:
            rho = rho.to(units)
        return rho

    def title(self):
        return Q_(self.x, "dimensionless")

    def update(self, p=None, T=None, h=None, s=None, x=None, **kwargs):
        if p is not None and T is not None:
            super().__init__(P=p.to("MPa").magnitude, T=T.to("degK").magnitude)
        elif p is not None and h is not None:
            super().__init__(P=p.to("MPa").magnitude, h=h.to("kJ/kg").magnitude)
        elif p is not None and s is not None:
            super().__init__(P=p.to("MPa").magnitude, s=s.to("kJ/(kg * degK)").magnitude)
        elif p is not None and x is not None:
            super().__init__(P=p.to("MPa").magnitude, x=x.magnitude)
        elif h is not None and s is not None:
            super().__init__(
                h=h.to("kJ/kg").magnitude, s=s.to("kJ/(kg * degK)").magnitude
            )
        elif T is not None and x is not None:
            super().__init__(T=T.to("degK").magnitude, x=x.magnitude)
        else:
            raise Exception("You did not pass the required parameters!")
