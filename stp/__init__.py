from pathlib import Path as _Path
import warnings as _warnings

###############################################################################
# pint
###############################################################################
import pint as _pint

_new_units = _Path(__file__).parent / "config/new_units.txt"
ureg = _pint.get_application_registry()
if isinstance(ureg.get(), _pint.registry.LazyRegistry):
    ureg = _pint.UnitRegistry()
    ureg.load_definitions(str(_new_units))
    # set ureg to make pickle possible
    _pint.set_application_registry(ureg)

Q_ = ureg.Quantity
_warnings.filterwarnings("ignore", message="The unit of the quantity is stripped")

from .state import State
from .turbine import SteamTurbine
from .point import Point

__all__ = ["State", "SteamTurbine", "Point"]
