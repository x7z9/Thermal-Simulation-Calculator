import numpy as np

def calculate_rectangular_fin_performance(P, Ac, L, k, h_conv, T_base, T_inf, n_points=100):
    """
    Calculates the performance of a rectangular fin with an adiabatic tip.

    Args:
        P (float): Perimeter of the fin (m)
        Ac (float): Cross-sectional area of the fin (m^2)
        L (float): Length of the fin (m)
        k (float): Thermal conductivity of the fin material (W/mK)
        h_conv (float): Convective heat transfer coefficient (W/m^2K)
        T_base (float): Temperature at the base of the fin (K)
        T_inf (float): Ambient fluid temperature (K)
        n_points (int, optional): Number of points for temperature distribution. Defaults to 100.

    Returns:
        dict: A dictionary containing:
            - x_coords (list): List of x-coordinates (from 0 to L).
            - temp_dist (list): List of temperatures T(x) corresponding to x_coords.
            - heat_transfer_rate (float): Calculated q_f.
            - fin_efficiency (float): Calculated eta_f.
    """
    if k <= 0 or Ac <= 0 or P <= 0: # prevent division by zero or sqrt of negative
        m = 0
    else:
        m = np.sqrt((h_conv * P) / (k * Ac))

    x_coords = np.linspace(0, L, n_points).tolist()

    # Temperature distribution
    # T(x) = T_inf + (T_base - T_inf) * (cosh(m * (L - x)) / cosh(m * L))
    # Handle T_base == T_inf case to avoid issues with cosh(0)/cosh(0) if m or L is also 0
    if T_base == T_inf:
        temp_dist = [T_inf] * n_points
    elif m == 0 or L == 0: # Handles cases where m*L might be zero, cosh(0)=1
        temp_dist = [T_base] * n_points # Uniform temperature
    else:
        temp_dist = [T_inf + (T_base - T_inf) * (np.cosh(m * (L - x_val)) / np.cosh(m * L)) for x_val in x_coords]

    # Heat transfer rate
    # q_f = sqrt(h_conv * P * k * Ac) * (T_base - T_inf) * tanh(m * L)
    if T_base == T_inf :
         q_f = 0.0
    elif m == 0 or L == 0: # if m or L is zero, tanh(m*L) is zero
        q_f = 0.0
    else:
        q_f = np.sqrt(h_conv * P * k * Ac) * (T_base - T_inf) * np.tanh(m * L)

    # Fin efficiency
    # eta_f = q_f / (h_conv * P * L * (T_base - T_inf))
    denominator_efficiency = h_conv * P * L * (T_base - T_inf)
    if T_base == T_inf: # q_f is 0
        eta_f = 1.0 # Or could be considered undefined, but problem asks for 1.
    elif denominator_efficiency == 0:
        eta_f = 1.0 # Avoid division by zero if L=0 or h_conv=0 or P=0
    else:
        eta_f = q_f / denominator_efficiency

    # Ensure efficiency is not greater than 1, which can happen due to precision with very small numbers
    # or if q_f is very slightly larger than the denominator due to floating point arithmetic.
    # Also handle cases where q_f might be negative if T_base < T_inf, though typically T_base >= T_inf for fins.
    # For this problem, we assume T_base >= T_inf, so q_f is positive.
    # If T_base < T_inf, q_f would be negative (heat into fin), and efficiency concept is different.
    # The problem implies T_base > T_inf from context of "heat transfer rate *from* the fin".
    eta_f = min(eta_f, 1.0) if eta_f > 0 else eta_f # clamp positive efficiency at 1
    # If q_f is 0 and T_base != T_inf, but h_conv*P*L is 0, eta_f will be 1.0 by prior rule.
    # If q_f is non-zero and h_conv*P*L is 0, this implies an issue, but caught by denominator_efficiency == 0.

    return {
        "x_coords": x_coords,
        "temp_dist": temp_dist,
        "heat_transfer_rate": q_f,
        "fin_efficiency": eta_f,
    }
