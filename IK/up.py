import numpy as np
import sympy as sp
from sympy import cos, sin, pi, symbols, Matrix, simplify, pprint
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
def visualize_robot_pose_enhanced(robot, joint_config):
    """Enhanced visualization that shows actual robot geometry"""
    T06, pos, rot, transforms = robot.forward_kinematics_numerical(joint_config)
    T01, T12, T23, T34, T45, T56 = transforms
    
    # Calculate all joint positions
    positions = [np.array([0, 0, 0, 1])]  # Base
    T_cumulative = np.eye(4)
    
    for T in transforms:
        T_cumulative = T_cumulative @ T
        joint_pos = T_cumulative @ np.array([0, 0, 0, 1])
        positions.append(joint_pos)
    
    # Extract x, y, z coordinates
    x_coords = [pos[0] for pos in positions]
    y_coords = [pos[1] for pos in positions] 
    z_coords = [pos[2] for pos in positions]
    
    # 3D plot with enhanced geometry
    fig = plt.figure(figsize=(15, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # 1. DRAW BASE (Cylinder)
    base_radius = 0.08
    base_height = 0.1
    z_base = np.linspace(0, base_height, 10)
    theta_base = np.linspace(0, 2*np.pi, 30)
    theta_grid, z_grid = np.meshgrid(theta_base, z_base)
    x_base = base_radius * np.cos(theta_grid)
    y_base = base_radius * np.sin(theta_grid)
    ax.plot_surface(x_base, y_base, z_grid, alpha=0.7, color='gray')
    
    # 2. DRAW SHOULDER JOINT (Sphere)
    shoulder_radius = 0.04
    u = np.linspace(0, 2 * np.pi, 20)
    v = np.linspace(0, np.pi, 20)
    x_sh = shoulder_radius * np.outer(np.cos(u), np.sin(v)) + x_coords[1]
    y_sh = shoulder_radius * np.outer(np.sin(u), np.sin(v)) + y_coords[1]
    z_sh = shoulder_radius * np.outer(np.ones(np.size(u)), np.cos(v)) + z_coords[1]
    ax.plot_surface(x_sh, y_sh, z_sh, alpha=0.8, color='red')
    
    # 3. DRAW UPPER ARM (Cylinder between shoulder and elbow)
    shoulder_pos = np.array([x_coords[1], y_coords[1], z_coords[1]])
    elbow_pos = np.array([x_coords[2], y_coords[2], z_coords[2]])
    arm_vector = elbow_pos - shoulder_pos
    arm_length = np.linalg.norm(arm_vector)
    
    if arm_length > 0:
        arm_direction = arm_vector / arm_length
        # Create cylinder for upper arm
        cylinder_radius = 0.02
        z_cyl = np.linspace(0, arm_length, 10)
        theta_cyl = np.linspace(0, 2*np.pi, 20)
        theta_g, z_g = np.meshgrid(theta_cyl, z_cyl)
        
        # Default cylinder along z-axis
        x_cyl = cylinder_radius * np.cos(theta_g)
        y_cyl = cylinder_radius * np.sin(theta_g)
        z_cyl = z_g
        
        # Rotate cylinder to match arm direction
        if not np.allclose(arm_direction, [0, 0, 1]):
            # Find rotation to align z-axis with arm direction
            z_axis = np.array([0, 0, 1])
            rotation_axis = np.cross(z_axis, arm_direction)
            rotation_axis_norm = np.linalg.norm(rotation_axis)
            if rotation_axis_norm > 1e-10:
                rotation_axis = rotation_axis / rotation_axis_norm
                rotation_angle = np.arccos(np.clip(np.dot(z_axis, arm_direction), -1, 1))
                
                # Apply rotation to cylinder points
                for i in range(x_cyl.shape[0]):
                    for j in range(x_cyl.shape[1]):
                        point = np.array([x_cyl[i,j], y_cyl[i,j], z_cyl[i,j]])
                        rotated_point = rotate_vector(point, z_axis, arm_direction)
                        x_cyl[i,j], y_cyl[i,j], z_cyl[i,j] = rotated_point
        
        # Translate cylinder to shoulder position
        x_cyl += shoulder_pos[0]
        y_cyl += shoulder_pos[1]
        z_cyl += shoulder_pos[2]
        
        ax.plot_surface(x_cyl, y_cyl, z_cyl, alpha=0.8, color='blue')
    
    # 4. DRAW ELBOW JOINT (Sphere)
    elbow_radius = 0.03
    x_el = elbow_radius * np.outer(np.cos(u), np.sin(v)) + x_coords[2]
    y_el = elbow_radius * np.outer(np.sin(u), np.sin(v)) + y_coords[2]
    z_el = elbow_radius * np.outer(np.ones(np.size(u)), np.cos(v)) + z_coords[2]
    ax.plot_surface(x_el, y_el, z_el, alpha=0.8, color='orange')
    
    # 5. DRAW FOREARM (Cylinder between elbow and wrist)
    elbow_pos = np.array([x_coords[2], y_coords[2], z_coords[2]])
    wrist_pos = np.array([x_coords[3], y_coords[3], z_coords[3]])
    forearm_vector = wrist_pos - elbow_pos
    forearm_length = np.linalg.norm(forearm_vector)
    
    if forearm_length > 0:
        forearm_direction = forearm_vector / forearm_length
        # Similar cylinder creation as above for forearm
        # ... (implementation similar to upper arm)
    
    # 6. DRAW TELESCOPIC ARM (Special rectangular prism)
    wrist_pos = np.array([x_coords[3], y_coords[3], z_coords[3]])
    wrist2_pos = np.array([x_coords[4], y_coords[4], z_coords[4]])
    telescopic_vector = wrist2_pos - wrist_pos
    telescopic_length = np.linalg.norm(telescopic_vector)
    
    # Draw telescopic arm as a rectangular prism
    prism_width = 0.03
    prism_depth = 0.03
    
    # 7. DRAW END-EFFECTOR
    ee_pos = np.array([x_coords[5], y_coords[5], z_coords[5]])
    # Draw gripper geometry
    
    # Plot original joint positions for reference
    ax.scatter(x_coords, y_coords, z_coords, c='red', s=80, label='Joint Centers')
    ax.plot(x_coords, y_coords, z_coords, 'k--', alpha=0.5, label='Joint Axis')
    
    # Coordinate frames
    ax.quiver(0, 0, 0, 0.1, 0, 0, color='red', linewidth=2, arrow_length_ratio=0.1)
    ax.quiver(0, 0, 0, 0, 0.1, 0, color='green', linewidth=2, arrow_length_ratio=0.1)
    ax.quiver(0, 0, 0, 0, 0, 0.1, color='blue', linewidth=2, arrow_length_ratio=0.1)
    
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.legend()
    ax.set_title('Enhanced Robot Visualization - Actual Geometry')
    
    # Set equal aspect ratio
    max_range = 1.5
    ax.set_xlim([-max_range, max_range])
    ax.set_ylim([-max_range, max_range])
    ax.set_zlim([0, max_range])
    
    plt.tight_layout()
    plt.show()

def rotate_vector(vector, from_dir, to_dir):
    """Rotate a vector from one direction to another"""
    # Normalize directions
    from_dir = from_dir / np.linalg.norm(from_dir)
    to_dir = to_dir / np.linalg.norm(to_dir)
    
    # If directions are parallel, no rotation needed
    if np.allclose(from_dir, to_dir):
        return vector
    
    # Calculate rotation axis and angle
    axis = np.cross(from_dir, to_dir)
    axis_norm = np.linalg.norm(axis)
    if axis_norm < 1e-10:
        return vector  # No rotation needed
    
    axis = axis / axis_norm
    angle = np.arccos(np.clip(np.dot(from_dir, to_dir), -1, 1))
    
    # Rodrigues' rotation formula
    cos_angle = np.cos(angle)
    sin_angle = np.sin(angle)
    
    rotated_vector = (vector * cos_angle + 
                     np.cross(axis, vector) * sin_angle + 
                     axis * np.dot(axis, vector) * (1 - cos_angle))
    
    return rotated_vector