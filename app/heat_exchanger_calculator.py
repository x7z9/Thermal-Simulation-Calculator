import numpy as np

def calculate_heat_exchanger_performance(m_dot_hot, Cp_hot, T_in_hot,
                                         m_dot_cold, Cp_cold, T_in_cold,
                                         UA, flow_type):
    """
    Calculates the performance of a heat exchanger using the NTU-effectiveness method.

    Args:
        m_dot_hot (float): Mass flow rate of the hot fluid (kg/s)
        Cp_hot (float): Specific heat capacity of the hot fluid (J/kgK)
        T_in_hot (float): Inlet temperature of the hot fluid (K)
        m_dot_cold (float): Mass flow rate of the cold fluid (kg/s)
        Cp_cold (float): Specific heat capacity of the cold fluid (J/kgK)
        T_in_cold (float): Inlet temperature of the cold fluid (K)
        UA (float): Overall heat transfer coefficient - Area product (W/K)
        flow_type (str): Type of flow ("parallel" or "counterflow")

    Returns:
        dict: A dictionary containing NTU, effectiveness, q_actual, T_out_hot, T_out_cold,
              and an optional error message.
    """
    results = {
        "NTU": None, "effectiveness": None, "q_actual": None,
        "T_out_hot": None, "T_out_cold": None, "error": None
    }

    if T_in_hot <= T_in_cold:
        results["error"] = "Hot fluid inlet temperature must be greater than cold fluid inlet temperature."
        # Still return calculated values if possible, or just error. For now, let's be strict.
        # Or, allow calculation but q_actual might be negative/zero.
        # The problem implies T_in_hot > T_in_cold for typical heat exchanger operation.
        # Let's make q_max positive by definition, so T_in_hot must be > T_in_cold.
        # If they are equal, q_max is 0, epsilon is irrelevant, q_actual is 0.
        if T_in_hot == T_in_cold:
             results["error"] = None # No error if temps are equal, q_actual will be 0
        else: # T_in_hot < T_in_cold
            return results


    C_hot = m_dot_hot * Cp_hot
    C_cold = m_dot_cold * Cp_cold

    results["T_out_hot"] = T_in_hot # Default if C_hot is 0 or q_actual is 0
    results["T_out_cold"] = T_in_cold # Default if C_cold is 0 or q_actual is 0


    if C_hot == 0 and C_cold == 0: # Both flow rates are zero
        results["NTU"] = 0 # Or undefined
        results["effectiveness"] = 0 # No heat transfer possible
        results["q_actual"] = 0.0
        results["error"] = "Both hot and cold fluid flow rates are zero. No heat transfer possible."
        return results

    if C_hot == 0 or C_cold == 0: # One of the flow rates is zero
        # This implies C_min is 0.
        C_min = 0
    elif C_hot < C_cold:
        C_min = C_hot
        C_max = C_cold
    else:
        C_min = C_cold
        C_max = C_hot

    if C_min == 0:
        results["NTU"] = float('inf') if UA > 0 else 0 # NTU = UA / C_min
        results["effectiveness"] = 0.0 # If C_min is 0, no heat can be transferred from the C_min stream's perspective of delta T
        results["q_actual"] = 0.0
        # error can be set to "One fluid has zero flow rate, no heat transfer."
        # However, q_max would be 0, so q_actual = epsilon * q_max = 0. This is consistent.
        # No need for an explicit error message if results are consistent.
        # The outlet temps will remain inlet temps as q_actual is 0.
        return results

    Cr = C_min / C_max  # Heat capacity ratio
    NTU = UA / C_min    # Number of Transfer Units
    results["NTU"] = NTU

    epsilon = 0.0
    if flow_type == "parallel":
        if Cr == 0: # Typically means one fluid is undergoing phase change (C_max -> inf) or C_min is extremely small
            epsilon = 1 - np.exp(-NTU)
        else:
            epsilon = (1 - np.exp(-NTU * (1 + Cr))) / (1 + Cr)
    elif flow_type == "counterflow":
        if Cr == 0: # Phase change on one side
             epsilon = 1 - np.exp(-NTU)
        elif Cr == 1:  # C_min == C_max
            epsilon = NTU / (1 + NTU)
        else:  # Cr < 1 and Cr != 0
            numerator = 1 - np.exp(-NTU * (1 - Cr))
            denominator = 1 - Cr * np.exp(-NTU * (1 - Cr))
            if denominator == 0: # Avoid division by zero if somehow exp term makes it zero
                epsilon = 1.0 # This implies perfect heat exchange for this specific condition
            else:
                epsilon = numerator / denominator
    else:
        results["error"] = "Invalid flow type specified. Must be 'parallel' or 'counterflow'."
        return results

    results["effectiveness"] = epsilon

    # Max possible heat transfer
    # q_max is defined based on the fluid with C_min, and the max temperature difference available.
    q_max = C_min * (T_in_hot - T_in_cold)
    if T_in_hot == T_in_cold: # q_max is 0, so q_actual is 0
        q_actual = 0.0
    else:
        q_actual = epsilon * q_max

    results["q_actual"] = q_actual

    # Outlet Temperatures
    # Ensure C_hot and C_cold are not zero before division
    if C_hot > 0:
        T_out_hot = T_in_hot - q_actual / C_hot
        results["T_out_hot"] = T_out_hot
    # else T_out_hot remains T_in_hot (already set or because q_actual should be 0 if C_hot led to C_min=0)

    if C_cold > 0:
        T_out_cold = T_in_cold + q_actual / C_cold
        results["T_out_cold"] = T_out_cold
    # else T_out_cold remains T_in_cold

    # Sanity check for temperatures (e.g., T_out_hot should not be < T_out_cold in normal operation)
    # This can happen if inputs are physically unrealistic or epsilon formula gives > 1 for some edge cases
    if results["T_out_hot"] is not None and results["T_out_cold"] is not None:
        if flow_type == "parallel" and results["T_out_hot"] < results["T_out_cold"]:
             # This should not happen if epsilon < 1. Could indicate an issue.
             # For parallel flow, T_out_hot must be >= T_out_cold.
             pass # Potentially add a warning or cap values.
        # For counterflow, T_out_hot can be < T_out_cold if hot fluid cools significantly
        # and cold fluid heats significantly, approaching each other's inlet temps.

    return results
