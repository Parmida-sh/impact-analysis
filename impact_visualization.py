import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.colors import Normalize
import matplotlib.cm as cm
from scipy.ndimage import gaussian_filter

# Physical parameters (fixed)
DISK_RADIUS = 30  # mm
DISK_THICKNESS = 0.5  # mm
GLASS_RADIUS = 300  # mm
GLASS_THICKNESS = 1.0  # mm

# Global smoothing state
smoothing_enabled = False

# Create figure with subplots
fig = plt.figure(figsize=(16, 11))
fig.suptitle('Steel Disk Impact on Hardened Glass Surface - Interactive Analysis', 
             fontsize=16, fontweight='bold')

# Main heatmap
ax_heatmap = plt.subplot(2, 2, (1, 3))
# Side view
ax_side = plt.subplot(2, 2, 2)

plt.subplots_adjust(bottom=0.40, right=0.85)

# Colormap with fixed range 0-500 MPa
cmap = plt.cm.RdYlBu_r
norm = Normalize(vmin=0, vmax=500)

def calculate_stress_field(force, repetitions, hardness, tilt_angle, smooth=False):
    """Calculate stress distribution on glass surface"""
    # Create meshgrid
    resolution = 100
    x = np.linspace(-GLASS_RADIUS, GLASS_RADIUS, resolution)
    y = np.linspace(-GLASS_RADIUS, GLASS_RADIUS, resolution)
    X, Y = np.meshgrid(x, y)
    
    # Distance from impact center
    R = np.sqrt(X**2 + Y**2)
    
    # Stress calculation based on contact mechanics
    # Effective force accounting for material properties
    effective_force = force * repetitions / (1 + hardness / 15)
    
    # Contact stress (Hertzian model)
    contact_radius = DISK_RADIUS
    max_stress = (effective_force * 1.5) / (np.pi * contact_radius**2)
    
    # Gaussian distribution for stress
    stress = np.zeros_like(R, dtype=float)
    
    # Within contact area
    mask1 = R <= contact_radius
    stress[mask1] = max_stress * np.exp(-(R[mask1]**2) / (2 * (contact_radius/2)**2))
    
    # Beyond contact area - decay
    mask2 = (R > contact_radius) & (R <= contact_radius * 2)
    decay = (R[mask2] - contact_radius) / contact_radius
    stress[mask2] = max_stress * np.exp(-decay**2) * 0.5
    
    # Tilt angle effect - add asymmetry
    if tilt_angle > 0:
        tilt_rad = np.radians(tilt_angle)
        asymmetry = 1 + 0.3 * (np.sin(np.arctan2(Y, X))) * (tilt_angle / 45)
        stress = stress * asymmetry
    
    # Apply smoothing if enabled
    if smooth:
        stress = gaussian_filter(stress, sigma=2.0)
    
    # Clamp to 0-500 MPa
    stress = np.clip(stress, 0, 500)
    
    return X, Y, stress

def calculate_side_profile(force, repetitions, hardness, tilt_angle, smooth=False):
    """Calculate stress profile along a cross-section"""
    resolution = 150
    distance = np.linspace(0, GLASS_RADIUS * 1.2, resolution)
    
    effective_force = force * repetitions / (1 + hardness / 15)
    contact_radius = DISK_RADIUS
    max_stress = (effective_force * 1.5) / (np.pi * contact_radius**2)
    
    stress = np.zeros_like(distance)
    
    # Within contact area
    mask1 = distance <= contact_radius
    stress[mask1] = max_stress * np.exp(-(distance[mask1]**2) / (2 * (contact_radius/2)**2))
    
    # Beyond contact area
    mask2 = (distance > contact_radius) & (distance <= contact_radius * 2)
    decay = (distance[mask2] - contact_radius) / contact_radius
    stress[mask2] = max_stress * np.exp(-decay**2) * 0.5
    
    # Apply smoothing if enabled
    if smooth:
        stress = gaussian_filter(stress, sigma=1.5)
    
    stress = np.clip(stress, 0, 500)
    
    # Surface deformation
    deformation = np.zeros_like(distance)
    deform_mask = distance <= contact_radius
    hardness_factor = 1 - (hardness - 5) / 10
    deformation[deform_mask] = (GLASS_THICKNESS * 0.2 * hardness_factor * 
                                 (1 - (distance[deform_mask] / contact_radius)**2))
    
    if smooth:
        deformation = gaussian_filter(deformation, sigma=1.5)
    
    return distance, stress, deformation

# Slider axes
ax_force = plt.axes([0.2, 0.32, 0.6, 0.03])
ax_reps = plt.axes([0.2, 0.27, 0.6, 0.03])
ax_hardness = plt.axes([0.2, 0.22, 0.6, 0.03])
ax_tilt = plt.axes([0.2, 0.17, 0.6, 0.03])

# Smoothing button
ax_smooth_btn = plt.axes([0.2, 0.11, 0.12, 0.04])
btn_smooth = Button(ax_smooth_btn, 'Smoothing: OFF', 
                    color='lightgray', hovercolor='#FF6B6B')

# Info button
ax_info_btn = plt.axes([0.35, 0.11, 0.12, 0.04])
btn_info = Button(ax_info_btn, 'ℹ️ Info', 
                  color='lightblue', hovercolor='#4ECDC4')

# Reset button
ax_reset_btn = plt.axes([0.50, 0.11, 0.12, 0.04])
btn_reset = Button(ax_reset_btn, 'Reset', 
                   color='lightgreen', hovercolor='#95E1D3')

# Create sliders
slider_force = Slider(ax_force, 'Force (N)', 1000, 50000, valinit=5000, valstep=500)
slider_reps = Slider(ax_reps, 'Repetitions', 1, 100, valinit=1, valstep=1)
slider_hardness = Slider(ax_hardness, 'Hardness (GPa)', 5, 15, valinit=8.5, valstep=0.5)
slider_tilt = Slider(ax_tilt, 'Tilt Angle (°)', 0, 45, valinit=0, valstep=1)

def toggle_smoothing(event):
    """Toggle smoothing on/off"""
    global smoothing_enabled
    smoothing_enabled = not smoothing_enabled
    
    if smoothing_enabled:
        btn_smooth.label.set_text('Smoothing: ON ✓')
        btn_smooth.color = '#90EE90'
        btn_smooth.hovercolor = '#98FB98'
    else:
        btn_smooth.label.set_text('Smoothing: OFF')
        btn_smooth.color = 'lightgray'
        btn_smooth.hovercolor = '#FF6B6B'
    
    update(None)

def show_info(event):
    """Show information about the simulation"""
    info_msg = (
        "═══ STEEL DISK IMPACT ANALYSIS ═══\n\n"
        "SPECIFICATIONS:\n"
        "  • Steel Disk: 30mm radius, 0.5mm thick\n"
        "  • Glass Surface: 300mm radius, 1mm thick\n"
        "  • Glass Type: Hardened (Borosilicate)\n\n"
        "CONTROLS:\n"
        "  • Force: Impact load (1K-50K N)\n"
        "  • Repetitions: Number of impacts\n"
        "  • Hardness: Glass material hardness (5-15 GPa)\n"
        "  • Tilt Angle: Disk angle at impact (0-45°)\n"
        "  • Smoothing: Apply Gaussian filter for physical smoothness\n\n"
        "VISUALIZATION:\n"
        "  Left: Top-view stress heatmap (0-500 MPa)\n"
        "  Right: Cross-section stress & deformation profile\n\n"
        "PHYSICS MODEL:\n"
        "  Uses Hertzian contact mechanics with material\n"
        "  property modulation for realistic stress distribution."
    )
    
    # Create info window
    info_fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis('off')
    ax.text(0.05, 0.95, info_msg, transform=ax.transAxes, 
            fontsize=10, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    info_fig.suptitle('Impact Analysis Guide', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show(block=False)

def reset_sliders(event):
    """Reset all sliders to default values"""
    slider_force.set_val(5000)
    slider_reps.set_val(1)
    slider_hardness.set_val(8.5)
    slider_tilt.set_val(0)
    global smoothing_enabled
    smoothing_enabled = False
    btn_smooth.label.set_text('Smoothing: OFF')
    btn_smooth.color = 'lightgray'
    btn_smooth.hovercolor = '#FF6B6B'
    update(None)

def update(val):
    """Update visualization based on slider values"""
    force = slider_force.val
    reps = int(slider_reps.val)
    hardness = slider_hardness.val
    tilt = slider_tilt.val
    
    # Calculate stress field
    X, Y, stress = calculate_stress_field(force, reps, hardness, tilt, smooth=smoothing_enabled)
    
    # Update heatmap
    ax_heatmap.clear()
    im = ax_heatmap.contourf(X, Y, stress, levels=20, cmap=cmap, norm=norm)
    ax_heatmap.contour(X, Y, stress, levels=10, colors='black', alpha=0.2, linewidths=0.5)
    
    # Add disk representation
    circle = plt.Circle((0, 0), DISK_RADIUS, color='red', fill=False, 
                         linewidth=2.5, linestyle='--', label='Disk Contact Area (30mm)')
    ax_heatmap.add_patch(circle)
    
    # Add outer glass boundary
    glass_circle = plt.Circle((0, 0), GLASS_RADIUS, color='blue', fill=False, 
                               linewidth=1.5, linestyle=':', alpha=0.6, label='Glass Boundary (300mm)')
    ax_heatmap.add_patch(glass_circle)
    
    ax_heatmap.set_xlabel('X (mm)', fontsize=11, fontweight='bold')
    ax_heatmap.set_ylabel('Y (mm)', fontsize=11, fontweight='bold')
    title = 'Top View: Stress Distribution (0-500 MPa)'
    if smoothing_enabled:
        title += ' [SMOOTHED]'
    ax_heatmap.set_title(title, fontsize=12, fontweight='bold')
    ax_heatmap.set_aspect('equal')
    ax_heatmap.legend(loc='upper right', fontsize=9)
    ax_heatmap.grid(True, alpha=0.2, linestyle='--')
    
    # Update side profile
    distance, stress_profile, deformation = calculate_side_profile(force, reps, hardness, tilt, 
                                                                    smooth=smoothing_enabled)
    
    ax_side.clear()
    ax_side_stress = ax_side
    ax_side_deform = ax_side.twinx()
    
    line1 = ax_side_stress.plot(distance, stress_profile, 'r-', linewidth=2.5, label='Stress', marker='o', markersize=3, markevery=15)
    ax_side_stress.fill_between(distance, 0, stress_profile, alpha=0.3, color='red')
    ax_side_stress.set_xlabel('Distance from Center (mm)', fontsize=10, fontweight='bold')
    ax_side_stress.set_ylabel('Stress (MPa)', color='r', fontsize=10, fontweight='bold')
    ax_side_stress.tick_params(axis='y', labelcolor='r')
    ax_side_stress.set_ylim([0, 500])
    ax_side_stress.grid(True, alpha=0.3, linestyle='--')
    
    line2 = ax_side_deform.plot(distance, deformation, 'b--', linewidth=2, label='Deformation', marker='s', markersize=3, markevery=15)
    ax_side_deform.set_ylabel('Deformation (mm)', color='b', fontsize=10, fontweight='bold')
    ax_side_deform.tick_params(axis='y', labelcolor='b')
    
    side_title = 'Cross-Section Profile'
    if smoothing_enabled:
        side_title += ' [SMOOTHED]'
    ax_side_stress.set_title(side_title, fontsize=12, fontweight='bold')
    
    # Combined legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax_side_stress.legend(lines, labels, loc='upper right', fontsize=9)
    
    # Add colorbar if not exists
    if not hasattr(fig, 'colorbar_ax'):
        cbar_ax = fig.add_axes([0.88, 0.35, 0.02, 0.5])
        fig.colorbar_ax = cbar_ax
        cb = fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), cax=cbar_ax)
        cb.set_label('Stress (MPa)', fontsize=11, fontweight='bold')
    
    # Update info text
    max_stress = stress.max()
    avg_stress = stress[stress > 0].mean()
    contact_area = np.pi * DISK_RADIUS**2
    total_force_contact = force * reps
    
    info_text = (f'Force: {force:.0f} N | Reps: {reps} | '
                 f'Hardness: {hardness:.1f} GPa | Tilt: {tilt:.0f}°\n'
                 f'Max Stress: {max_stress:.1f} MPa | Avg Stress: {avg_stress:.1f} MPa | '
                 f'Contact Area: {contact_area:.1f} mm² | Total Force: {total_force_contact:.0f} N')
    
    if hasattr(fig, 'info_text'):
        fig.info_text.remove()
    
    fig.info_text = fig.text(0.5, 0.04, info_text, ha='center', fontsize=9.5, 
                             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
    
    fig.canvas.draw_idle()

# Connect buttons to functions
btn_smooth.on_clicked(toggle_smoothing)
btn_info.on_clicked(show_info)
btn_reset.on_clicked(reset_sliders)

# Connect sliders to update function
slider_force.on_changed(update)
slider_reps.on_changed(update)
slider_hardness.on_changed(update)
slider_tilt.on_changed(update)

# Initial plot
update(None)

# Add instructions
instruction_text = ("Press 'Smoothing' to toggle Gaussian smoothing | 'ℹ️ Info' for guide | 'Reset' to restore defaults")
fig.text(0.5, 0.005, instruction_text, ha='center', fontsize=9, style='italic', color='gray')

plt.show()
