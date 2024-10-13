import stp

from stp import Q_

p_i = Q_(42, "bar")
T_i = Q_(350, "degC")

p_d = Q_(0.01, "bar")

inlet = stp.State(p=p_i, T=T_i)

print(inlet.enthalpy())