import numpy as np
from scipy.optimize import differential_evolution
from logging import warning

from . import Q_
from .point import Point
from .state import State

class SteamTurbine:
    
    coef_list = ["enthalpy_coeff", "volume_ratio", "phi", "phi_disch"]

    def __init__(self, guaranteed, test_point, divergence_limit=None) -> None:
        
        if divergence_limit is None:
            divergence_limit = 5
            
        self.divergence_limits_dict = {}
        for k in self.coef_list:
            self.divergence_limits_dict[k] = divergence_limit

        self.guaranteed = guaranteed
    
        validation_dict = self.check_points(test_point)
        valid = all([v["passed"] for k, v in validation_dict.items()])
        setattr(test_point, "valid", valid)         
        self.test_results = {
            "point": test_point,
            "valid": valid,
            "result": validation_dict
        }

        self.test_point = test_point
        self.output = None

        units_dict = {}

        for k in dir(test_point):
            if not k.startswith("_"):
                if isinstance(getattr(test_point, k), State):
                    state_obj = getattr(test_point, k)
                    for p in dir(state_obj):
                        try:
                            var_unit = getattr(state_obj, p)().u
                            if p == "enthalpy":
                                units_dict["h_unit"] = var_unit
                            elif p == "entropy":
                                units_dict["s_unit"] = var_unit
                            elif p == "density":
                                units_dict["rho_unit"] = var_unit
                            elif p == "title":
                                units_dict["x_unit"] = var_unit
                            else:
                                units_dict[f"{p[0]}_unit"] = var_unit
                        except (AttributeError, TypeError, Exception):
                            continue
                else:
                    try:
                        var_unit = getattr(test_point, k)().u
                        units_dict[f"{k}_unit"] = var_unit
                    except (AttributeError, TypeError, Exception):
                        continue

        self.units_dict = units_dict


    def check_points(self, point):

        validation_dict = {}
        
        for k in self.coef_list:
            coef_guaranteed = getattr(self.guaranteed, k).m
            coef_test = getattr(point, k).m
            relative_difference = self._relative_difference(coef_guaranteed, coef_test) * 100
            
            validation_dict[k] = {
                "passed": bool(relative_difference <= self.divergence_limits_dict[k]),
                "value": relative_difference
            }        

        return validation_dict

    def _relative_difference(self, target, predict):

        return np.abs(target - predict) / target

    def find_test_conditions(self, bounds, update_point=True, **kwargs):
        default_params = ["p", "T", "disch_p", "flow_m"]
        parameters_list = kwargs.get("parameters", default_params)
        
        def objective_func(x):
            test_point = self._mount_point(parameters_list, x)
            guaranteed_coefs = []
            test_coefs = []

            for k in self.coef_list:
                guaranteed_coefs.append(getattr(self.guaranteed, k).m)
                test_coefs.append(getattr(test_point, k).m)

            sum = np.sum(self._relative_difference(np.array(guaranteed_coefs), np.array(test_coefs)))
            return sum
        
        results = differential_evolution(objective_func, bounds=bounds, tol=1e-6)
        final_point = self._mount_point(parameters_list, results.x)
        validation_dict = self.check_points(final_point)
        valid = all([v["passed"] for k, v in validation_dict.items()])

        self.print_compare(final_point)

        if valid:
            if update_point:
                self.test_point = final_point
        else:
            print("")
            warning("\nThe optimization did not found a valid combination! The test can not be performed based on the referred bounds!")
        
        return self.test_point

    def _mount_point(self, parameters, x):
        inlet_dict = {}
        test_dict = {}
        for j, param in enumerate(parameters):
            if param == "p":
                inlet_dict[param] = Q_(x[j], "bar")
            elif param == "T":
                inlet_dict[param] = Q_(x[j], "degC")
            else:
                unit = getattr(self.test_point, param).u
                test_dict[param] = Q_(x[j], unit)

        point = Point(
            inlet=State(**inlet_dict),
            eff=self.guaranteed.eff,
            **test_dict
        )

        return point
    
    def save_txt(self, file):
        if self.output is None:
            self.print_compare()

        with open(file, "w") as f:
            f.write("\n".join(self.output))
    
    def print_compare(self, point=None):

        if point is None:
            point = self.test_point
            test_results = self.test_results["result"]
        else:
            test_results = self.check_points(point)

        msg = [
            "Parameters",
            "----------",
            f"Speed:     {point.speed:.3f}",
            f"Title:     {point.disch.title().m:.3f} @ test | {self.guaranteed.disch.title().m:.3f} @ guaranteed",
            f"Flow:      {point.flow_m:.3f}",
            f"Inlet:     {point.inlet.pressure().to('bar'):.3f} @ {point.inlet.temperature().to('degC'):.3f}",
            f"Discharge: {point.disch.pressure().to('bar'):.3f} @ {point.disch.temperature().to('degC'):.3f}",
        ]
        titles = ["Enthalpy Coefficient", "Volume Ratio", "Flow Coefficient - Inlet", "Flow Coefficient - Discharge"]
        for k, title in enumerate(titles):
            guaranteed_txt = f"Guaranteed:  {getattr(self.guaranteed, self.coef_list[k]).m:.3f}"
            point_txt = f"Test:        {getattr(point, self.coef_list[k]).m:.3f}"
            error_txt = f"Error (%):   {test_results[self.coef_list[k]]['value']:.3f}"
            
            msg.append("\n"+title)
            msg.append("-" * len(title))
            msg.append(guaranteed_txt)
            msg.append(point_txt)
            msg.append(error_txt)

        print(*msg, sep="\n")
        self.output = msg