document.addEventListener('DOMContentLoaded', function () {
    const compositeWallForm = document.getElementById('compositeWallForm');
    const layersContainer = document.getElementById('layers-container');
    const addLayerBtn = document.getElementById('addLayerBtn');
    const layerTemplate = document.getElementById('layerTemplate');

    const totalResistanceEl = document.getElementById('totalResistance');
    const heatFluxEl = document.getElementById('heatFlux');
    const errorMessagesEl = document.getElementById('errorMessages');
    const exportPdfBtnComposite = document.getElementById('exportPdfBtnComposite'); // Added

    let layerCounter = 0;
    let currentInputs_comp = {}; // For PDF
    let currentOutputs_comp = {}; // For PDF

    function addLayer() {
        layerCounter++;
        const newLayer = layerTemplate.cloneNode(true);
        newLayer.style.display = 'block';
        newLayer.id = `layer-${layerCounter}`;
        newLayer.querySelector('.layer-number').textContent = layerCounter;

        // Set unique names for inputs for easier processing if needed, though we'll iterate
        newLayer.querySelector('.layer-thickness').name = `layer_${layerCounter}_thickness`;
        newLayer.querySelector('.layer-k_value').name = `layer_${layerCounter}_k_value`;
        newLayer.querySelector('.layer-area').name = `layer_${layerCounter}_area`;

        const removeBtn = newLayer.querySelector('.removeLayerBtn');
        removeBtn.addEventListener('click', function () {
            removeLayer(newLayer);
        });

        layersContainer.appendChild(newLayer);
    }

    function removeLayer(layerElement) {
        layersContainer.removeChild(layerElement);
        // Renumber layers visually if needed, though not strictly necessary for functionality
        const remainingLayers = layersContainer.querySelectorAll('.layer-number');
        remainingLayers.forEach((span, index) => {
            span.textContent = index + 1;
        });
        layerCounter = layersContainer.children.length; // Update counter based on actual children
    }

    addLayerBtn.addEventListener('click', addLayer);

    // Add one layer by default
    addLayer();

    compositeWallForm.addEventListener('submit', async function (event) {
        event.preventDefault();
        errorMessagesEl.textContent = '';
        totalResistanceEl.textContent = '---';
        heatFluxEl.textContent = '---';
        exportPdfBtnComposite.style.display = 'none'; // Hide button

        currentInputs_comp.T_inner = parseFloat(document.getElementById('T_inner').value);
        currentInputs_comp.T_outer = parseFloat(document.getElementById('T_outer').value);

        if (isNaN(currentInputs_comp.T_inner) || isNaN(currentInputs_comp.T_outer)) {
            errorMessagesEl.textContent = 'Inner and Outer Temperatures must be valid numbers.';
            return;
        }

        const layersData = [];
        const layerElements = layersContainer.children;

        if (layerElements.length === 0) {
            errorMessagesEl.textContent = 'At least one layer must be added.';
            return;
        }

        let validLayers = true;
        currentInputs_comp.layers = []; // Reset layers for current inputs

        for (let i = 0; i < layerElements.length; i++) {
            const layerDiv = layerElements[i];
            if (!layerDiv.id || !layerDiv.id.startsWith('layer-')) continue;

            const thickness = parseFloat(layerDiv.querySelector('.layer-thickness').value);
            const k_value = parseFloat(layerDiv.querySelector('.layer-k_value').value);
            const area = parseFloat(layerDiv.querySelector('.layer-area').value);

            if (isNaN(thickness) || isNaN(k_value) || isNaN(area)) {
                errorMessagesEl.textContent = `Layer ${i + 1}: All fields must be valid numbers.`;
                validLayers = false;
                break;
            }
            if (thickness < 0) {
                errorMessagesEl.textContent = `Layer ${i + 1}: Thickness must be non-negative.`;
                validLayers = false;
                break;
            }
            if (k_value <= 0) {
                errorMessagesEl.textContent = `Layer ${i + 1}: Thermal Conductivity (k) must be positive.`;
                validLayers = false;
                break;
            }
            if (area <= 0) {
                errorMessagesEl.textContent = `Layer ${i + 1}: Area must be positive.`;
                validLayers = false;
                break;
            }
            layersData.push({ thickness, k_value, area });
            currentInputs_comp.layers.push({ name: `Layer ${i+1}`, thickness, k_value, area }); // For PDF
        }

        if (!validLayers) {
            return;
        }

        const payload = { // Payload for fetch
            layers: layersData, // This should be the simple list of objects for the backend
            T_inner: currentInputs_comp.T_inner,
            T_outer: currentInputs_comp.T_outer
        };

        try {
            const response = await fetch('/calculate_composite_wall', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            const data = await response.json();

            if (response.ok) {
                totalResistanceEl.textContent = data.total_resistance.toFixed(4);
                currentOutputs_comp["Total Thermal Resistance (R_total) [K/W]"] = data.total_resistance.toFixed(4);

                if (data.heat_flux !== null) {
                    heatFluxEl.textContent = data.heat_flux.toFixed(4);
                    currentOutputs_comp["Heat Flux (q_flux) [W/m^2]"] = data.heat_flux.toFixed(4);
                } else {
                    heatFluxEl.textContent = "N/A (Infinite or Undefined)";
                    currentOutputs_comp["Heat Flux (q_flux) [W/m^2]"] = "N/A (Infinite or Undefined)";
                }
                 // Store individual resistances for PDF if needed
                currentOutputs_comp.individual_resistances = data.individual_resistances.map((r, i) => `Layer ${i+1} Resistance: ${r.toFixed(4)} K/W`);


                exportPdfBtnComposite.style.display = 'inline-block'; // Show button
                if(data.error){
                    errorMessagesEl.textContent = `Note: ${data.error}`; // Display backend warning
                }
            } else {
                errorMessagesEl.textContent = `Error: ${data.error || 'Calculation failed.'}`;
                exportPdfBtnComposite.style.display = 'none';
            }
        } catch (error) {
            console.error('Fetch error:', error);
            errorMessagesEl.textContent = 'An error occurred while fetching data. Please check the console.';
            exportPdfBtnComposite.style.display = 'none';
        }
    });

    exportPdfBtnComposite.addEventListener('click', function() {
        if (!currentInputs_comp.T_inner || Object.keys(currentOutputs_comp).length === 0) {
            alert("Please perform a calculation first to generate data for the PDF.");
            return;
        }

        const inputsForPdf = [
            { name: "Inner Surface Temperature (T_inner) [K]", value: currentInputs_comp.T_inner.toString() },
            { name: "Outer Surface Temperature (T_outer) [K]", value: currentInputs_comp.T_outer.toString() }
        ];

        currentInputs_comp.layers.forEach(layer => {
            inputsForPdf.push({ name: `${layer.name} - Thickness (m)`, value: layer.thickness.toString() });
            inputsForPdf.push({ name: `${layer.name} - K-value (W/mK)`, value: layer.k_value.toString() });
            inputsForPdf.push({ name: `${layer.name} - Area (m^2)`, value: layer.area.toString() });
        });

        const outputsForPdf = [
             { name: "Total Thermal Resistance (R_total) [K/W]", value: currentOutputs_comp["Total Thermal Resistance (R_total) [K/W]"]},
             { name: "Heat Flux (q_flux) [W/m^2]", value: currentOutputs_comp["Heat Flux (q_flux) [W/m^2]"]}
        ];
        if(currentOutputs_comp.individual_resistances) {
            currentOutputs_comp.individual_resistances.forEach(r_str => {
                const parts = r_str.split(': ');
                outputsForPdf.push({name: parts[0], value: parts[1]});
            });
        }


        const pdfData = {
            calculator_name: "Composite Wall Calculator Report",
            inputs: inputsForPdf,
            outputs: outputsForPdf,
            notes: "Area is assumed constant for all layers in this calculation."
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
            a.download = "composite_wall_report.pdf";
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
