document.addEventListener('DOMContentLoaded', function () {
    const heatExchangerForm = document.getElementById('heatExchangerForm');

    // Result elements
    const ntuResultEl = document.getElementById('NTU_result');
    const effectivenessResultEl = document.getElementById('effectiveness_result');
    const qActualResultEl = document.getElementById('q_actual_result');
    const tOutHotResultEl = document.getElementById('T_out_hot_result');
    const tOutColdResultEl = document.getElementById('T_out_cold_result');
    const errorMessagesEl = document.getElementById('errorMessages');
    const exportPdfBtnHE = document.getElementById('exportPdfBtnHE'); // Added

    let currentInputs_he = {}; // For PDF
    let currentOutputs_he = {}; // For PDF

    heatExchangerForm.addEventListener('submit', async function (event) {
        event.preventDefault();

        // Clear previous results and errors
        ntuResultEl.textContent = '---';
        effectivenessResultEl.textContent = '---';
        qActualResultEl.textContent = '---';
        tOutHotResultEl.textContent = '---';
        tOutColdResultEl.textContent = '---';
        errorMessagesEl.textContent = '';
        exportPdfBtnHE.style.display = 'none'; // Hide button

        // Get values and store for PDF
        currentInputs_he = {
            m_dot_hot: parseFloat(document.getElementById('m_dot_hot').value),
            Cp_hot: parseFloat(document.getElementById('Cp_hot').value),
            T_in_hot: parseFloat(document.getElementById('T_in_hot').value),
            m_dot_cold: parseFloat(document.getElementById('m_dot_cold').value),
            Cp_cold: parseFloat(document.getElementById('Cp_cold').value),
            T_in_cold: parseFloat(document.getElementById('T_in_cold').value),
            UA: parseFloat(document.getElementById('UA').value),
            flow_type: document.getElementById('flow_type').value
        };

        // Frontend validation
        const numericalInputs = { // Exclude flow_type for this check
            m_dot_hot: currentInputs_he.m_dot_hot,
            Cp_hot: currentInputs_he.Cp_hot,
            T_in_hot: currentInputs_he.T_in_hot,
            m_dot_cold: currentInputs_he.m_dot_cold,
            Cp_cold: currentInputs_he.Cp_cold,
            T_in_cold: currentInputs_he.T_in_cold,
            UA: currentInputs_he.UA
        };

        for (const key in numericalInputs) {
            if (isNaN(numericalInputs[key])) {
                errorMessagesEl.textContent = `All input fields (except flow type) must be filled with valid numbers. Error with: ${key}`;
                return;
            }
             if (key !== 'T_in_hot' && key !== 'T_in_cold' && numericalInputs[key] < 0) {
                 errorMessagesEl.textContent = `Parameter '${key}' must be non-negative.`;
                 return;
            }
        }

        if (currentInputs_he.T_in_hot <= currentInputs_he.T_in_cold) {
            errorMessagesEl.textContent = 'Hot fluid inlet temperature (T_in_hot) must be greater than cold fluid inlet temperature (T_in_cold) for meaningful heat exchange in this model.';
        }

        const payload = currentInputs_he; // Use the stored inputs

        try {
            const response = await fetch('/calculate_heat_exchanger', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            const data = await response.json();

            if (response.ok) {
                currentOutputs_he = {
                    "NTU": data.NTU !== null ? data.NTU.toFixed(4) : 'N/A',
                    "Effectiveness (ε)": data.effectiveness !== null ? data.effectiveness.toFixed(4) : 'N/A',
                    "Actual Heat Transfer Rate (q_actual) [W]": data.q_actual !== null ? data.q_actual.toFixed(2) : 'N/A',
                    "Hot Fluid Outlet Temperature (T_out_hot) [K]": data.T_out_hot !== null ? data.T_out_hot.toFixed(2) : 'N/A',
                    "Cold Fluid Outlet Temperature (T_out_cold) [K]": data.T_out_cold !== null ? data.T_out_cold.toFixed(2) : 'N/A'
                };

                ntuResultEl.textContent = currentOutputs_he.NTU;
                effectivenessResultEl.textContent = currentOutputs_he["Effectiveness (ε)"];
                qActualResultEl.textContent = currentOutputs_he["Actual Heat Transfer Rate (q_actual) [W]"];
                tOutHotResultEl.textContent = currentOutputs_he["Hot Fluid Outlet Temperature (T_out_hot) [K]"];
                tOutColdResultEl.textContent = currentOutputs_he["Cold Fluid Outlet Temperature (T_out_cold) [K]"];

                exportPdfBtnHE.style.display = 'inline-block'; // Show button
                if(data.error && !response.ok) { // Only show as primary error if response not ok
                     errorMessagesEl.textContent = `Error: ${data.error}`;
                } else if (data.error) { // Show as note if response ok but backend has a warning
                     errorMessagesEl.textContent = `Note: ${data.error}`;
                }

            } else {
                errorMessagesEl.textContent = `Error: ${data.error || 'Calculation failed.'}`;
                exportPdfBtnHE.style.display = 'none';
            }
        } catch (error) {
            console.error('Fetch error:', error);
            errorMessagesEl.textContent = 'An error occurred while fetching data. Please check the console.';
            exportPdfBtnHE.style.display = 'none';
        }
    });

    exportPdfBtnHE.addEventListener('click', function() {
        if (Object.keys(currentInputs_he).length === 0 || Object.keys(currentOutputs_he).length === 0) {
            alert("Please perform a calculation first to generate data for the PDF.");
            return;
        }

        const inputsForPdf = Object.entries(currentInputs_he).map(([key, value]) => {
            const labelElement = document.querySelector(`label[for="${key}"]`);
            let name = key;
            if (labelElement) { // Get full label text
                name = labelElement.textContent.replace(/:$/, '');
            } else { // Fallback for flow_type or if label not found
                if (key === "m_dot_hot") name = "Hot Fluid Mass Flow Rate (ṁ_hot) [kg/s]";
                else if (key === "Cp_hot") name = "Hot Fluid Specific Heat (Cp_hot) [J/kgK]";
                else if (key === "T_in_hot") name = "Hot Fluid Inlet Temperature (T_in_hot) [K]";
                else if (key === "m_dot_cold") name = "Cold Fluid Mass Flow Rate (ṁ_cold) [kg/s]";
                else if (key === "Cp_cold") name = "Cold Fluid Specific Heat (Cp_cold) [J/kgK]";
                else if (key === "T_in_cold") name = "Cold Fluid Inlet Temperature (T_in_cold) [K]";
                else if (key === "UA") name = "Overall Heat Transfer Coefficient-Area (UA) [W/K]";
                else if (key === "flow_type") name = "Flow Type";
            }
            return { name, value: value.toString() };
        });

        const pdfData = {
            calculator_name: "Heat Exchanger Performance Report",
            inputs: inputsForPdf,
            outputs: Object.entries(currentOutputs_he).map(([name, value]) => ({ name, value: value.toString() })),
            notes: "Calculations performed using the NTU-effectiveness method."
        };

        fetch('/export_pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(pdfData)
        })
        .then(response => {
            if (!response.ok) {
                 return response.json().then(err => { throw new Error(err.error || `PDF generation failed with status: ${response.status}`) });
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = "heat_exchanger_report.pdf";
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('PDF Export Error:', error);
            errorMessagesEl.textContent = `PDF Export Error: ${error.message}`;
        });
    });
});
