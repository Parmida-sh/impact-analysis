import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from matplotlib.colors import Normalize
import matplotlib.cm as cm

# Physical parameters (fixed)
DISK_RADIUS = 30  # mm
DISK_THICKNESS = 0.5  # mm
GLASS_RADIUS = 300  # mm
GLASS_THICKNESS = 1.0  # mm

# Create figure with subplots
fig = plt.figure(figsize=(15, 10))
fig.suptitle('Steel Disk Impact on Hardened Glass Surface', fontsize=16, fontweight='bold')

# Main heatmap
ax_heatmap = plt.subplot(2, 2, (1, 3))
# Side view
ax_side = plt.subplot(2, 2, 2)

plt.subplots_adjust(bottom=0.35, right=0.85)

# Colormap with fixed range 0-500 MPa
cmap = plt.cm.RdYlBu_r
norm = Normalize(vmin=0, vmax=500)

def calculate_stress_field(force, repetitions, hardness, tilt_angle):
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
    
    # Clamp to 0-500 MPa
    stress = np.clip(stress, 0, 500)
    
    return X, Y, stress

def calculate_side_profile(force, repetitions, hardness, tilt_angle):
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
    
    stress = np.clip(stress, 0, 500)
    
    # Surface deformation
    deformation = np.zeros_like(distance)
    deform_mask = distance <= contact_radius
    hardness_factor = 1 - (hardness - 5) / 10
    deformation[deform_mask] = (GLASS_THICKNESS * 0.2 * hardness_factor * 
                                 (1 - (distance[deform_mask] / contact_radius)**2))
    
    return distance, stress, deformation

# Slider axes
ax_force = plt.axes([0.2, 0.25, 0.6, 0.03])
ax_reps = plt.axes([0.2, 0.20, 0.6, 0.03])
ax_hardness = plt.axes([0.2, 0.15, 0.6, 0.03])
ax_tilt = plt.axes([0.2, 0.10, 0.6, 0.03])

# Create sliders
slider_force = Slider(ax_force, 'Force (N)', 1000, 50000, valinit=5000, valstep=500)
slider_reps = Slider(ax_reps, 'Repetitions', 1, 100, valinit=1, valstep=1)
slider_hardness = Slider(ax_hardness, 'Hardness (GPa)', 5, 15, valinit=8.5, valstep=0.5)
slider_tilt = Slider(ax_tilt, 'Tilt Angle (°)', 0, 45, valinit=0, valstep=1)

def update(val):
    """Update visualization based on slider values"""
    force = slider_force.val
    reps = int(slider_reps.val)
    hardness = slider_hardness.val
    tilt = slider_tilt.val
    
    # Calculate stress field
    X, Y, stress = calculate_stress_field(force, reps, hardness, tilt)
    
    # Update heatmap
    ax_heatmap.clear()
    im = ax_heatmap.contourf(X, Y, stress, levels=20, cmap=cmap, norm=norm)
    ax_heatmap.contour(X, Y, stress, levels=10, colors='black', alpha=0.2, linewidths=0.5)
    
    # Add disk representation
    circle = plt.Circle((0, 0), DISK_RADIUS, color='red', fill=False, 
                         linewidth=2, linestyle='--', label='Disk Contact Area')
    ax_heatmap.add_patch(circle)
    
    ax_heatmap.set_xlabel('X (mm)', fontsize=11)
    ax_heatmap.set_ylabel('Y (mm)', fontsize=11)
    ax_heatmap.set_title('Top View: Stress Distribution (0-500 MPa)', fontsize=12, fontweight='bold')
    ax_heatmap.set_aspect('equal')
    ax_heatmap.legend(loc='upper right')
    ax_heatmap.grid(True, alpha=0.3)
    
    # Update side profile
    distance, stress_profile, deformation = calculate_side_profile(force, reps, hardness, tilt)
    
    ax_side.clear()
    ax_side_stress = ax_side
    ax_side_deform = ax_side.twinx()
    
    line1 = ax_side_stress.plot(distance, stress_profile, 'r-', linewidth=2.5, label='Stress')
    ax_side_stress.fill_between(distance, 0, stress_profile, alpha=0.3, color='red')
    ax_side_stress.set_xlabel('Distance (mm)', fontsize=10)
    ax_side_stress.set_ylabel('Stress (MPa)', color='r', fontsize=10)
    ax_side_stress.tick_params(axis='y', labelcolor='r')
    ax_side_stress.set_ylim([0, 500])
    ax_side_stress.grid(True, alpha=0.3)
    
    line2 = ax_side_deform.plot(distance, deformation, 'b--', linewidth=2, label='Deformation')
    ax_side_deform.set_ylabel('Deformation (mm)', color='b', fontsize=10)
    ax_side_deform.tick_params(axis='y', labelcolor='b')
    
    ax_side_stress.set_title('Cross-Section Profile', fontsize=12, fontweight='bold')
    
    # Combined legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax_side_stress.legend(lines, labels, loc='upper right', fontsize=9)
    
    # Add colorbar
    if not hasattr(fig, 'colorbar_ax'):
        cbar_ax = fig.add_axes([0.88, 0.35, 0.02, 0.5])
        fig.colorbar_ax = cbar_ax
        cb = fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), cax=cbar_ax)
        cb.set_label('Stress (MPa)', fontsize=11)
    
    # Update info text
    info_text = (f'Force: {force:.0f} N | Reps: {reps} | '
                 f'Hardness: {hardness:.1f} GPa | Tilt: {tilt:.0f}°\n'
                 f'Max Stress: {stress.max():.1f} MPa | '
                 f'Avg Stress: {stress[stress > 0].mean():.1f} MPa')
    fig.text(0.5, 0.02, info_text, ha='center', fontsize=10, 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    fig.canvas.draw_idle()

# Connect sliders to update function
slider_force.on_changed(update)
slider_reps.on_changed(update)
slider_hardness.on_changed(update)
slider_tilt.on_changed(update)

# Initial plot
update(None)

plt.show()
