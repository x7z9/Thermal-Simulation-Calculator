from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        # Optional: Add a header if desired
        # self.set_font("Arial", "B", 12)
        # self.cell(0, 10, "ThermalSim Suite Report", 0, 1, "C")
        pass

    def footer(self):
        # Optional: Add a page footer
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

def generate_thermal_report_pdf(data):
    """
    Generates a PDF report from the given data.

    Args:
        data (dict): A dictionary containing:
            - calculator_name (str): Title of the report section.
            - inputs (list): List of tuples [(name, value), ...] for input parameters.
            - outputs (list): List of tuples [(name, value), ...] for calculated results.
            - notes (str, optional): Additional notes for the report.

    Returns:
        bytes: The PDF content as bytes.
    """
    pdf = PDF() # Use custom PDF class if header/footer are defined
    pdf.add_page()

    # Main Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, data.get('calculator_name', 'Thermal Calculation Report'), 0, 1, "C")
    pdf.ln(10)

    # Inputs Section
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Input Parameters:", 0, 1)
    pdf.set_font("Arial", "", 10)
    if isinstance(data.get('inputs'), list):
        for name, value in data['inputs']:
            pdf.cell(0, 7, f"{name}: {value}", 0, 1)
    elif isinstance(data.get('inputs'), dict): # Also allow dict for inputs
        for name, value in data['inputs'].items():
            pdf.cell(0, 7, f"{name}: {value}", 0, 1)
    pdf.ln(5)

    # Outputs Section
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Calculated Results:", 0, 1)
    pdf.set_font("Arial", "", 10)
    if isinstance(data.get('outputs'), list):
        for name, value in data['outputs']:
            pdf.cell(0, 7, f"{name}: {value}", 0, 1)
    elif isinstance(data.get('outputs'), dict): # Also allow dict for outputs
         for name, value in data['outputs'].items():
            pdf.cell(0, 7, f"{name}: {value}", 0, 1)
    pdf.ln(5)

    # Notes Section
    notes = data.get('notes')
    if notes:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Notes:", 0, 1)
        pdf.set_font("Arial", "I", 10)
        pdf.multi_cell(0, 7, str(notes))
        pdf.ln(5)

    # Timestamp
    from datetime import datetime
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, "C")

    return pdf.output(dest='S').encode('latin-1')
