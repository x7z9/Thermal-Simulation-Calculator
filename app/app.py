from flask import Flask, request, jsonify, render_template
from flask import Response # Added Response
from app.fin_calculator import calculate_rectangular_fin_performance
from app.composite_wall_calculator import calculate_composite_wall_performance
from app.heat_exchanger_calculator import calculate_heat_exchanger_performance
from app.pdf_generator import generate_thermal_report_pdf # Added PDF generator

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fin-calculator')
def fin_calculator_page():
    return render_template('fin_calculator.html')

@app.route('/calculate_fin', methods=['POST'])
def calculate_fin_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        required_params = ['P', 'Ac', 'L', 'k', 'h_conv', 'T_base', 'T_inf']
        missing_params = [param for param in required_params if param not in data]
        if missing_params:
            return jsonify({"error": f"Missing parameters: {', '.join(missing_params)}"}), 400

        P = data['P']
        Ac = data['Ac']
        L = data['L']
        k = data['k']
        h_conv = data['h_conv']
        T_base = data['T_base']
        T_inf = data['T_inf']
        n_points = data.get('n_points', 100) # Optional parameter

        # Basic type checking and value validation
        numerical_params = {'P': P, 'Ac': Ac, 'L': L, 'k': k, 'h_conv': h_conv, 'T_base': T_base, 'T_inf': T_inf}
        for name, value in numerical_params.items():
            if not isinstance(value, (int, float)):
                return jsonify({"error": f"Parameter '{name}' must be a number."}), 400

        if not isinstance(n_points, int) or n_points <= 0:
             return jsonify({"error": "Parameter 'n_points' must be a positive integer."}), 400


        # Add specific constraints based on physical reality if necessary
        if Ac <= 0:
            return jsonify({"error": "Cross-sectional area 'Ac' must be positive."}), 400
        if P <= 0:
            return jsonify({"error": "Perimeter 'P' must be positive."}), 400
        if k <= 0:
            return jsonify({"error": "Thermal conductivity 'k' must be positive."}), 400
        # L can be 0, h_conv can be 0. T_base and T_inf can be equal.

        results = calculate_rectangular_fin_performance(
            P=float(P), Ac=float(Ac), L=float(L), k=float(k),
            h_conv=float(h_conv), T_base=float(T_base), T_inf=float(T_inf),
            n_points=int(n_points)
        )
        return jsonify(results), 200

    except TypeError as e: # Catches errors if data is not JSON or other type issues
        return jsonify({"error": f"Invalid input type or data format: {str(e)}"}), 400
    except Exception as e:
        # Log the exception e for debugging
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/composite-wall-calculator')
def composite_wall_calculator_page():
    return render_template('composite_wall_calculator.html')


if __name__ == '__main__':
    # Note: This typically runs on port 5000 by default
    app.run(debug=True)

@app.route('/export_pdf', methods=['POST'])
def export_pdf_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided for PDF generation."}), 400

        # Basic validation for required fields in data
        required_fields = ['calculator_name', 'inputs', 'outputs']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing data for PDF generation: {', '.join(missing_fields)}"}), 400

        # Ensure inputs and outputs are lists of tuples/lists or dicts
        # For simplicity, pdf_generator handles list of tuples or dicts.
        # Here we just check they exist and are of a list/dict type.
        if not (isinstance(data['inputs'], (list, dict)) and isinstance(data['outputs'], (list, dict))):
             return jsonify({"error": "'inputs' and 'outputs' must be lists or dictionaries."}), 400


        pdf_bytes = generate_thermal_report_pdf(data)

        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": "attachment;filename=thermal_report.pdf"}
        )
    except Exception as e:
        # Log the exception e for debugging
        # import traceback
        # traceback.print_exc()
        return jsonify({"error": f"An error occurred during PDF generation: {str(e)}"}), 500


@app.route('/calculate_heat_exchanger', methods=['POST'])
def calculate_heat_exchanger_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        required_params = [
            'm_dot_hot', 'Cp_hot', 'T_in_hot',
            'm_dot_cold', 'Cp_cold', 'T_in_cold',
            'UA', 'flow_type'
        ]
        missing_params = [param for param in required_params if param not in data]
        if missing_params:
            return jsonify({"error": f"Missing parameters: {', '.join(missing_params)}"}), 400

        params = {}
        numerical_param_names = ['m_dot_hot', 'Cp_hot', 'T_in_hot', 'm_dot_cold', 'Cp_cold', 'T_in_cold', 'UA']

        for p_name in numerical_param_names:
            val = data[p_name]
            if not isinstance(val, (int, float)):
                return jsonify({"error": f"Parameter '{p_name}' must be a number."}), 400
            if p_name not in ['T_in_hot', 'T_in_cold'] and val <= 0: # m_dot, Cp, UA must be positive
                 # m_dot can be 0 for C_min=0 case, but problem asked for positive.
                 # Let's allow non-negative for m_dot, Cp to handle C_min=0 (no flow)
                 if val < 0 : # Strictly negative is an error.
                    return jsonify({"error": f"Parameter '{p_name}' must be non-negative."}), 400
                 # If m_dot or Cp is 0, C_hot or C_cold will be 0, handled by calculator.
            params[p_name] = float(val)

        flow_type = data.get('flow_type')
        if flow_type not in ["parallel", "counterflow"]:
            return jsonify({"error": "Parameter 'flow_type' must be 'parallel' or 'counterflow'."}), 400
        params['flow_type'] = flow_type

        # Specific validation for temperatures if needed, e.g. T_in_hot > T_in_cold
        # The calculator function itself has a check for T_in_hot > T_in_cold.
        # if params['T_in_hot'] <= params['T_in_cold']:
        #     return jsonify({"error": "T_in_hot must be strictly greater than T_in_cold for effective heat exchange."}), 400


        results = calculate_heat_exchanger_performance(
            m_dot_hot=params['m_dot_hot'], Cp_hot=params['Cp_hot'], T_in_hot=params['T_in_hot'],
            m_dot_cold=params['m_dot_cold'], Cp_cold=params['Cp_cold'], T_in_cold=params['T_in_cold'],
            UA=params['UA'], flow_type=params['flow_type']
        )

        if results.get("error"):
            return jsonify({"error": results["error"]}), 400

        return jsonify(results), 200

    except TypeError as e: # Catches errors if data is not JSON or other type issues
        return jsonify({"error": f"Invalid input type or data format: {str(e)}"}), 400
    except Exception as e:
        # Log the exception e for debugging
        # import traceback
        # traceback.print_exc()
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/heat-exchanger-calculator')
def heat_exchanger_calculator_page():
    return render_template('heat_exchanger_calculator.html')

@app.route('/calculate_composite_wall', methods=['POST'])
def calculate_composite_wall_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        layers_data = data.get('layers')
        T_inner = data.get('T_inner')
        T_outer = data.get('T_outer')

        if not isinstance(layers_data, list) or not layers_data:
            return jsonify({"error": "Parameter 'layers' must be a non-empty list."}), 400
        if not all(isinstance(layer, dict) for layer in layers_data):
            return jsonify({"error": "Each item in 'layers' must be a dictionary."}), 400

        validated_layers = []
        for i, layer in enumerate(layers_data):
            thickness = layer.get('thickness')
            k_value = layer.get('k_value')
            area = layer.get('area')

            if not all(isinstance(val, (int, float)) for val in [thickness, k_value, area]):
                return jsonify({"error": f"Layer {i+1}: 'thickness', 'k_value', and 'area' must be numbers."}), 400
            if thickness < 0: # Allow thickness = 0 for potential surface resistances
                 return jsonify({"error": f"Layer {i+1}: 'thickness' must be non-negative."}), 400
            if k_value <= 0:
                 return jsonify({"error": f"Layer {i+1}: 'k_value' must be positive."}), 400
            if area <= 0:
                 return jsonify({"error": f"Layer {i+1}: 'area' must be positive."}), 400
            validated_layers.append({'thickness': float(thickness), 'k_value': float(k_value), 'area': float(area)})

        if not all(isinstance(temp, (int, float)) for temp in [T_inner, T_outer]):
            return jsonify({"error": "'T_inner' and 'T_outer' must be numbers."}), 400

        results = calculate_composite_wall_performance(
            layers=validated_layers,
            T_inner=float(T_inner),
            T_outer=float(T_outer)
        )

        if results.get("error"):
            # Determine status code based on error if needed, otherwise default to 400 for client-side correctable errors
            # or 500 if it's an unrecoverable issue from the calculator's perspective
            status_code = 400 # Default for calculation issues based on input
            if "infinite heat flux" in results["error"]: # Example of a more specific error
                status_code = 400
            return jsonify({"error": results["error"]}), status_code

        return jsonify(results), 200

    except TypeError as e: # Catches errors if data is not JSON or other type issues
        return jsonify({"error": f"Invalid input type or data format: {str(e)}"}), 400
    except Exception as e:
        # Log the exception e for debugging
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
