import numpy as np

def calculate_composite_wall_performance(layers, T_inner, T_outer):
    """
    Calculates the heat conduction performance for a composite wall.

    Args:
        layers (list): A list of dictionaries, where each dictionary represents a layer
                       and contains 'thickness' (m), 'k_value' (W/mK), and 'area' (m^2).
        T_inner (float): Temperature at the inner surface of the wall (K).
        T_outer (float): Temperature at the outer surface of the wall (K).

    Returns:
        dict: A dictionary containing:
            - total_resistance (float): Calculated R_total.
            - heat_flux (float or None): Calculated q_flux. None if R_total is 0 and deltaT is not 0.
            - individual_resistances (list): List of R_layer for each layer.
            - error (str, optional): Error message if R_total is 0 and deltaT is not 0.
    """
    individual_resistances = []
    R_total = 0.0

    if not layers:
        return {
            "total_resistance": 0,
            "heat_flux": 0, # Or None, depending on how we want to define this for no wall
            "individual_resistances": [],
            "error": "No layers provided for the wall."
        }

    for layer in layers:
        thickness = layer.get('thickness')
        k_value = layer.get('k_value')
        area = layer.get('area')

        # This basic validation should ideally be in the Flask route
        # but good to have a safeguard here too.
        if thickness is None or k_value is None or area is None:
            return {
                "total_resistance": None, "heat_flux": None, "individual_resistances": [],
                "error": "Each layer must have 'thickness', 'k_value', and 'area'."
            }
        if k_value <= 0 or area <= 0 or thickness < 0: # thickness can be 0 for a surface resistance, though not typical for wall layers
             return {
                "total_resistance": None, "heat_flux": None, "individual_resistances": [],
                "error": "k_value and area must be positive, thickness must be non-negative."
            }

        # If thickness is 0, R_layer is 0 (useful for contact resistances, though not explicitly asked)
        # If k_value or area were 0 (which validation should prevent), this would cause ZeroDivisionError
        R_layer = thickness / (k_value * area) if k_value * area != 0 else float('inf') if thickness > 0 else 0
        if R_layer == float('inf'):
            return {
                "total_resistance": float('inf'), "heat_flux": 0, "individual_resistances": [float('inf') if r.get('thickness',0)/(r.get('k_value',1)*r.get('area',1)) == float('inf') else r.get('thickness',0)/(r.get('k_value',1)*r.get('area',1)) for r in layers], #recalculate for display
                "error": "A layer has zero k_value or area, leading to infinite resistance."
            }

        individual_resistances.append(R_layer)
        R_total += R_layer

    delta_T = T_inner - T_outer
    heat_flux = None
    error_message = None

    if R_total == 0:
        if delta_T == 0:
            heat_flux = 0.0
        else:
            # This case implies infinite heat flux, which is problematic.
            # Or it could mean layers have zero thickness, meaning direct contact.
            error_message = "Total thermal resistance is zero with a non-zero temperature difference. This implies infinite heat flux or direct contact with zero resistance layers."
            # heat_flux remains None
    else:
        heat_flux = delta_T / R_total

    result = {
        "total_resistance": R_total,
        "heat_flux": heat_flux,
        "individual_resistances": individual_resistances
    }
    if error_message:
        result["error"] = error_message

    return result
