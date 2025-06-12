document.addEventListener('DOMContentLoaded', function () {
    const finForm = document.getElementById('finForm');
    const heatTransferRateEl = document.getElementById('heatTransferRate');
    const finEfficiencyEl = document.getElementById('finEfficiency');
    const errorMessagesEl = document.getElementById('errorMessages');
    const exportPdfBtn = document.getElementById('exportPdfBtn'); // Added
    const ctx = document.getElementById('tempDistChart').getContext('2d');
    let tempDistChart = null;
    let currentInputs = {}; // To store inputs for PDF export
    let currentOutputs = {}; // To store outputs for PDF export

    finForm.addEventListener('submit', async function (event) {
        event.preventDefault();
        errorMessagesEl.textContent = ''; // Clear previous errors
        exportPdfBtn.style.display = 'none'; // Hide PDF button until results are ready

        // Store inputs for potential PDF export
        currentInputs = {
            P: parseFloat(document.getElementById('P').value),
            Ac: parseFloat(document.getElementById('Ac').value),
            L: parseFloat(document.getElementById('L').value),
            k: parseFloat(document.getElementById('k').value),
            h_conv: parseFloat(document.getElementById('h_conv').value),
            T_base: parseFloat(document.getElementById('T_base').value),
            T_inf: parseFloat(document.getElementById('T_inf').value)
        };

        // Basic frontend validation using currentInputs
        if (Object.values(currentInputs).some(isNaN)) {
            errorMessagesEl.textContent = 'All input fields must be filled with valid numbers.';
            return;
        }
        if (currentInputs.P <= 0) {
            errorMessagesEl.textContent = 'Fin Perimeter (P) must be positive.';
            return;
        }
        if (currentInputs.Ac <= 0) {
            errorMessagesEl.textContent = 'Fin Cross-sectional Area (Ac) must be positive.';
            return;
        }
         if (currentInputs.L < 0) {
            errorMessagesEl.textContent = 'Fin Length (L) must be non-negative.';
            return;
        }
        if (currentInputs.k <= 0) {
            errorMessagesEl.textContent = 'Thermal Conductivity (k) must be positive.';
            return;
        }
        if (currentInputs.h_conv < 0) {
            errorMessagesEl.textContent = 'Convection Coefficient (h_conv) must be non-negative.';
            return;
        }
         if (currentInputs.T_base <= 0 || currentInputs.T_inf <= 0) {
            errorMessagesEl.textContent = 'Temperatures (T_base, T_inf) must be positive (in Kelvin).';
            return;
        }

        const payload = currentInputs; // Use the stored inputs for the fetch payload

        try {
            const response = await fetch('/calculate_fin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            const data = await response.json();

            if (response.ok) {
                heatTransferRateEl.textContent = data.heat_transfer_rate.toFixed(4);
                finEfficiencyEl.textContent = data.fin_efficiency.toFixed(4);

                // Store outputs for PDF export
                currentOutputs = {
                    "Heat Transfer Rate (q_f) [W]": data.heat_transfer_rate.toFixed(4),
                    "Fin Efficiency (η_f)": data.fin_efficiency.toFixed(4),
                    // Note: Temperature distribution is graphical and not included in text outputs for PDF.
                };
                exportPdfBtn.style.display = 'inline-block'; // Show PDF button since results are available

                if (tempDistChart) {
                    tempDistChart.destroy();
                }

                tempDistChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.x_coords.map(x => x.toFixed(3)),
                        datasets: [{
                            label: 'Temperature Distribution',
                            data: data.temp_dist.map(t => t.toFixed(2)),
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1,
                            fill: false
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            x: {
                                title: {
                                    display: true,
                                    text: 'Distance along fin (m)'
                                }
                            },
                            y: {
                                title: {
                                    display: true,
                                    text: 'Temperature (K)'
                                }
                            }
                        }
                    }
                });
            } else {
                errorMessagesEl.textContent = `Error: ${data.error || 'Calculation failed.'}`;
                heatTransferRateEl.textContent = '---';
                finEfficiencyEl.textContent = '---';
                exportPdfBtn.style.display = 'none'; // Hide PDF button on error
                if (tempDistChart) {
                    tempDistChart.destroy();
                    tempDistChart = null;
                }
            }
        } catch (error) {
            console.error('Fetch error:', error);
            errorMessagesEl.textContent = 'An error occurred while fetching data. Please check the console.';
            heatTransferRateEl.textContent = '---';
            finEfficiencyEl.textContent = '---';
            exportPdfBtn.style.display = 'none'; // Hide PDF button on error
             if (tempDistChart) {
                tempDistChart.destroy();
                tempDistChart = null;
            }
        }
    });

    // Event listener for the PDF export button
    exportPdfBtn.addEventListener('click', function() {
        if (Object.keys(currentInputs).length === 0 || Object.keys(currentOutputs).length === 0) {
            alert("Please perform a calculation first to generate data for the PDF.");
            return;
        }

        // Prepare data for PDF generation
        const pdfData = {
            calculator_name: "Fin Calculator Report",
            inputs: Object.entries(currentInputs).map(([key, value]) => {
                // Attempt to get the label text for a more descriptive name
                const labelElement = document.querySelector(`label[for="${key}"]`);
                const name = labelElement ? labelElement.textContent.replace(/:$/, '') : key; // Remove trailing colon if present
                return { name, value: value.toString() };
            }),
            outputs: Object.entries(currentOutputs).map(([name, value]) => ({ name, value: value.toString() })),
            notes: "The temperature distribution along the fin is a graphical result and is not included in this PDF summary."
        };

        // Fetch request to the backend to generate and download the PDF
        fetch('/export_pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(pdfData)
        })
        .then(response => {
            if (!response.ok) {
                // Try to get error message from backend if available
                return response.json().then(err => { throw new Error(err.error || `PDF generation failed with status: ${response.status}`) });
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = "fin_calculator_report.pdf"; // Suggested filename
            document.body.appendChild(a);
            a.click();
            a.remove(); // Clean up the DOM
            window.URL.revokeObjectURL(url); // Free up memory
        })
        .catch(error => {
            console.error('PDF Export Error:', error);
            errorMessagesEl.textContent = `PDF Export Error: ${error.message}`;
        });
    });
});
