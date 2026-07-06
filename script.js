// Material Properties
const STEEL_DISK = {
    radius: 30,      // mm
    thickness: 0.5,  // mm
    youngsModulus: 200000,  // MPa
    poissonRatio: 0.3
};

const GLASS_SURFACE = {
    radius: 300,     // mm
    thickness: 1,    // mm
    youngsModulus: 70000,   // MPa
    poissonRatio: 0.22
};

// Fixed scale for heatmap (0 to 1000 MPa)
const STRESS_SCALE_MIN = 0;
const STRESS_SCALE_MAX = 1000;

// Slider elements
const forceSlider = document.getElementById('forceSlider');
const repetitionsSlider = document.getElementById('repetitionsSlider');
const hardnessSlider = document.getElementById('hardnessSlider');
const tiltSlider = document.getElementById('tiltSlider');

// Value display elements
const forceValue = document.getElementById('forceValue');
const repetitionsValue = document.getElementById('repetitionsValue');
const hardnessValue = document.getElementById('hardnessValue');
const tiltValue = document.getElementById('tiltValue');

// Stats elements
const contactAreaElement = document.getElementById('contactArea');
const maxStressElement = document.getElementById('maxStress');

// Initialize
updateVisualization();

// Event listeners
forceSlider.addEventListener('input', function() {
    forceValue.textContent = this.value;
    updateVisualization();
});

repetitionsSlider.addEventListener('input', function() {
    repetitionsValue.textContent = this.value;
    updateVisualization();
});

hardnessSlider.addEventListener('input', function() {
    hardnessValue.textContent = parseFloat(this.value).toFixed(1);
    updateVisualization();
});

tiltSlider.addEventListener('input', function() {
    tiltValue.textContent = this.value;
    updateVisualization();
});

function calculateContactArea(force, tiltAngle) {
    // Hertzian contact calculation
    // For a disk on a flat surface, contact area approximation
    const effectiveRadius = (STEEL_DISK.radius * GLASS_SURFACE.radius) / 
                           (STEEL_DISK.radius + GLASS_SURFACE.radius);
    
    // Modified for tilt angle (reduces contact area)
    const tiltFactor = Math.cos(tiltAngle * Math.PI / 180);
    
    // Effective Young's modulus
    const E_eff = 1 / ((1 - STEEL_DISK.poissonRatio**2) / STEEL_DISK.youngsModulus + 
                       (1 - GLASS_SURFACE.poissonRatio**2) / GLASS_SURFACE.youngsModulus);
    
    // Contact radius using Hertzian formula
    const contactRadius = Math.cbrt((3 * force * effectiveRadius) / (4 * E_eff)) * tiltFactor;
    
    return Math.PI * contactRadius ** 2;
}

function calculateStressDistribution(force, tiltAngle, hardness, repetitions, gridSize = 100) {
    const contactArea = calculateContactArea(force, tiltAngle);
    const contactRadius = Math.sqrt(contactArea / Math.PI);
    
    // Maximum contact stress (Hertzian)
    const maxContactStress = (3 * force) / (2 * Math.PI * contactArea);
    
    // Apply hardness multiplier (higher hardness reduces stress)
    const effectiveStress = maxContactStress / hardness;
    
    // Apply repetition factor (cumulative damage)
    const cumulativeStress = effectiveStress * Math.sqrt(repetitions);
    
    // Create 2D stress distribution
    const stressData = [];
    const xRange = Array.from({length: gridSize}, (_, i) => 
        -GLASS_SURFACE.radius/2 + (i * GLASS_SURFACE.radius) / gridSize);
    const yRange = Array.from({length: gridSize}, (_, i) => 
        -GLASS_SURFACE.radius/2 + (i * GLASS_SURFACE.radius) / gridSize);
    
    // Tilt angle affects stress distribution center
    const tiltOffsetX = (tiltAngle * STEEL_DISK.radius) / 45;
    
    for (let i = 0; i < gridSize; i++) {
        const row = [];
        for (let j = 0; j < gridSize; j++) {
            const x = xRange[j];
            const y = yRange[i];
            
            // Distance from impact center (adjusted for tilt)
            const dist = Math.sqrt((x - tiltOffsetX)**2 + y**2);
            
            // Stress distribution following Hertzian approximation
            if (dist < contactRadius * 1.5) {
                // Gaussian-like distribution centered at contact
                const normalizedDist = dist / contactRadius;
                const stress = cumulativeStress * Math.exp(-normalizedDist**2 * 2);
                row.push(Math.max(0, stress));
            } else {
                row.push(0);
            }
        }
        stressData.push(row);
    }
    
    return {
        data: stressData,
        contactRadius: contactRadius,
        maxStress: cumulativeStress,
        contactArea: contactArea
    };
}

function updateVisualization() {
    const force = parseFloat(forceSlider.value);
    const repetitions = parseFloat(repetitionsSlider.value);
    const hardness = parseFloat(hardnessSlider.value);
    const tiltAngle = parseFloat(tiltSlider.value);
    
    // Calculate stress distribution
    const stressAnalysis = calculateStressDistribution(force, tiltAngle, hardness, repetitions, 120);
    
    // Update stats
    contactAreaElement.textContent = stressAnalysis.contactArea.toFixed(2);
    maxStressElement.textContent = stressAnalysis.maxStress.toFixed(1);
    
    // Update heatmap
    updateHeatmap(stressAnalysis, tiltAngle);
    
    // Update cross-section
    updateCrossSection(stressAnalysis);
}

function updateHeatmap(stressAnalysis, tiltAngle) {
    const stressData = stressAnalysis.data;
    const gridSize = stressData.length;
    
    // Create x and y axes (in mm)
    const xRange = Array.from({length: gridSize}, (_, i) => 
        -GLASS_SURFACE.radius/2 + (i * GLASS_SURFACE.radius) / gridSize);
    const yRange = Array.from({length: gridSize}, (_, i) => 
        -GLASS_SURFACE.radius/2 + (i * GLASS_SURFACE.radius) / gridSize);
    
    // Create heatmap trace
    const heatmapTrace = {
        z: stressData,
        x: xRange,
        y: yRange,
        type: 'heatmap',
        colorscale: [
            [0, '#0d47a1'],      // Dark blue - low stress
            [0.25, '#1976d2'],   // Blue
            [0.5, '#42a5f5'],    // Light blue
            [0.65, '#64b5f6'],   // Lighter blue
            [0.75, '#ffeb3b'],   // Yellow
            [0.85, '#ff9800'],   // Orange
            [0.95, '#f44336'],   // Red
            [1, '#c62828']       // Dark red - high stress
        ],
        zmin: STRESS_SCALE_MIN,
        zmax: STRESS_SCALE_MAX,
        colorbar: {
            title: 'Stress (MPa)',
            thickness: 20,
            len: 0.7,
            x: 1.02
        },
        hovertemplate: 'X: %{x:.1f} mm<br>Y: %{y:.1f} mm<br>Stress: %{z:.1f} MPa<extra></extra>'
    };
    
    // Add contact circle annotation
    const contactRadius = stressAnalysis.contactRadius;
    const tiltOffsetX = (tiltAngle * STEEL_DISK.radius) / 45;
    
    const layout = {
        title: {
            text: `Stress Heatmap on Glass Surface | Tilt: ${tiltAngle}°`,
            font: { size: 14 }
        },
        xaxis: { title: 'X (mm)', showgrid: true, zeroline: true },
        yaxis: { title: 'Y (mm)', showgrid: true, zeroline: true },
        width: null,
        height: 500,
        hovermode: 'closest',
        margin: { b: 60, l: 60, r: 150, t: 60 },
        shapes: [
            {
                type: 'circle',
                x0: tiltOffsetX - contactRadius,
                y0: -contactRadius,
                x1: tiltOffsetX + contactRadius,
                y1: contactRadius,
                line: {
                    color: 'rgba(255, 255, 255, 0.8)',
                    width: 2,
                    dash: 'dash'
                },
                fillcolor: 'rgba(0, 0, 0, 0)'
            }
        ]
    };
    
    Plotly.newPlot('heatmap', [heatmapTrace], layout, {responsive: true});
}

function updateCrossSection(stressAnalysis) {
    const stressData = stressAnalysis.data;
    const gridSize = stressData.length;
    const contactRadius = stressAnalysis.contactRadius;
    
    // Get center row for cross-section
    const centerRow = Math.floor(gridSize / 2);
    const crossSectionStress = stressData[centerRow];
    
    // Create x-axis (distance from center)
    const xRange = Array.from({length: gridSize}, (_, i) => 
        -GLASS_SURFACE.radius/2 + (i * GLASS_SURFACE.radius) / gridSize);
    
    // Create trace
    const trace = {
        x: xRange,
        y: crossSectionStress,
        type: 'scatter',
        mode: 'lines',
        name: 'Stress Distribution',
        line: {
            color: '#667eea',
            width: 3
        },
        fill: 'tozeroy',
        fillcolor: 'rgba(102, 126, 234, 0.2)',
        hovertemplate: 'Position: %{x:.1f} mm<br>Stress: %{y:.1f} MPa<extra></extra>'
    };
    
    // Add reference lines
    const shapes = [
        // Contact radius left
        {
            type: 'line',
            x0: -contactRadius,
            y0: 0,
            x1: -contactRadius,
            y1: stressAnalysis.maxStress,
            line: { color: 'rgba(255, 152, 0, 0.5)', width: 2, dash: 'dot' }
        },
        // Contact radius right
        {
            type: 'line',
            x0: contactRadius,
            y0: 0,
            x1: contactRadius,
            y1: stressAnalysis.maxStress,
            line: { color: 'rgba(255, 152, 0, 0.5)', width: 2, dash: 'dot' }
        }
    ];
    
    const layout = {
        title: {
            text: 'Cross-Section Stress Distribution',
            font: { size: 14 }
        },
        xaxis: { title: 'Distance from Center (mm)', zeroline: true, showgrid: true },
        yaxis: { 
            title: 'Stress (MPa)',
            range: [0, STRESS_SCALE_MAX],
            showgrid: true
        },
        width: null,
        height: 300,
        hovermode: 'x unified',
        margin: { b: 50, l: 60, r: 40, t: 50 },
        shapes: shapes,
        annotations: [
            {
                x: -contactRadius,
                y: stressAnalysis.maxStress * 0.95,
                text: `Contact Radius<br>${contactRadius.toFixed(2)} mm`,
                showarrow: true,
                arrowhead: 2,
                arrowsize: 1,
                arrowwidth: 2,
                arrowcolor: '#ff9800',
                ax: -40,
                ay: -30,
                font: { size: 10, color: '#ff9800' }
            }
        ]
    };
    
    Plotly.newPlot('crossSection', [trace], layout, {responsive: true});
}

// Responsive resize
window.addEventListener('resize', updateVisualization);