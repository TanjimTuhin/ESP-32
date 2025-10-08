import numpy as np
import sympy as sp
from sympy import cos, sin, pi, symbols, Matrix, simplify, pprint
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class RobotKinematics:
    def __init__(self):
        """Initialize the 6-DOF robot kinematics solver"""
        # Define symbolic variables
        self.theta1, self.theta2, self.theta3, self.theta5, self.theta6 = symbols('theta1 theta2 theta3 theta5 theta6')
        self.d4 = symbols('d4')  # Prismatic joint variable
        self.dof = 6  # Add this
        # Robot parameters (from DH table)
        self.d1 = 0.1      # Base height
        self.a2 = 0.338    # First arm segment
        self.a3 = 0.171    # Second arm segment  
        self.d4_min = 0.282  # Minimum telescopic extension
        self.d5 = 0.095    # Wrist segment 1
        self.d6 = 0.226    # Wrist segment 2 (end-effector)
        
    def get_transformation_matrix(self, theta, d, a, alpha):
        """Standard DH transformation matrix"""
        return Matrix([
            [cos(theta), -sin(theta)*cos(alpha), sin(theta)*sin(alpha), a*cos(theta)],
            [sin(theta), cos(theta)*cos(alpha), -cos(theta)*sin(alpha), a*sin(theta)],
            [0, sin(alpha), cos(alpha), d],
            [0, 0, 0, 1]
        ])
    
    def get_all_transforms(self):
        """Get all individual transformation matrices"""
        # Joint 1: Revolute (θ₁, d=0.1, a=0, α=π/2)
        T01 = self.get_transformation_matrix(self.theta1, self.d1, 0, pi/2)
        
        # Joint 2: Revolute (θ₂, d=0, a=0.338, α=0)
        T12 = self.get_transformation_matrix(self.theta2, 0, self.a2, 0)
        
        # Joint 3: Revolute (θ₃, d=0, a=0.171, α=0)  
        T23 = self.get_transformation_matrix(self.theta3, 0, self.a3, 0)
        
        # Joint 4: Prismatic (θ=0, d=d₄, a=0, α=π/2)
        T34 = self.get_transformation_matrix(0, self.d4, 0, pi/2)
        
        # Joint 5: Revolute (θ₅, d=0.095, a=0, α=-π/2)
        T45 = self.get_transformation_matrix(self.theta5, self.d5, 0, -pi/2)
        
        # Joint 6: Revolute (θ₆, d=0.226, a=0, α=0)
        T56 = self.get_transformation_matrix(self.theta6, self.d6, 0, 0)
        
        return T01, T12, T23, T34, T45, T56
    
    def forward_kinematics_symbolic(self):
        """Compute symbolic forward kinematics"""
        T01, T12, T23, T34, T45, T56 = self.get_all_transforms()
        
        # Chain multiplication: T₀⁶ = T₀¹ × T₁² × T₂³ × T₃⁴ × T₄⁵ × T₅⁶
        T06 = T01 * T12 * T23 * T34 * T45 * T56
        
        return T06, (T01, T12, T23, T34, T45, T56)
    
    def forward_kinematics_numerical(self, joint_values):
        """
        Compute numerical forward kinematics
        joint_values: [theta1, theta2, theta3, d4, theta5, theta6] in radians and meters
        """
        t1, t2, t3, d4_val, t5, t6 = joint_values
        
        # Check telescopic joint limits
        if d4_val < self.d4_min:
            print(f"Warning: d4={d4_val:.3f} below minimum {self.d4_min:.3f}")
            d4_val = self.d4_min
        elif d4_val > 0.647:
            print(f"Warning: d4={d4_val:.3f} above maximum 0.647")
            d4_val = 0.647
        
        # Numerical transformation matrices
        T01 = np.array([
            [np.cos(t1), 0, np.sin(t1), 0],
            [np.sin(t1), 0, -np.cos(t1), 0], 
            [0, 1, 0, self.d1],
            [0, 0, 0, 1]
        ])
        
        T12 = np.array([
            [np.cos(t2), -np.sin(t2), 0, self.a2*np.cos(t2)],
            [np.sin(t2), np.cos(t2), 0, self.a2*np.sin(t2)],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        T23 = np.array([
            [np.cos(t3), -np.sin(t3), 0, self.a3*np.cos(t3)],
            [np.sin(t3), np.cos(t3), 0, self.a3*np.sin(t3)],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        T34 = np.array([
            [1, 0, 0, 0],
            [0, 0, -1, 0],
            [0, 1, 0, d4_val],
            [0, 0, 0, 1]
        ])
        
        T45 = np.array([
            [np.cos(t5), 0, -np.sin(t5), 0],
            [np.sin(t5), 0, np.cos(t5), 0],
            [0, -1, 0, self.d5],
            [0, 0, 0, 1]
        ])
        
        T56 = np.array([
            [np.cos(t6), -np.sin(t6), 0, 0],
            [np.sin(t6), np.cos(t6), 0, 0],
            [0, 0, 1, self.d6],
            [0, 0, 0, 1]
        ])
        
        # Chain multiplication
        T06 = T01 @ T12 @ T23 @ T34 @ T45 @ T56
        
        # Extract position and orientation
        position = T06[:3, 3]
        rotation_matrix = T06[:3, :3]
        
        return T06, position, rotation_matrix, (T01, T12, T23, T34, T45, T56)
    
    def get_workspace_limits(self):
        """Calculate approximate workspace limits"""
        # Maximum reach (all joints extended)
        max_reach = self.a2 + self.a3 + 0.647 + self.d5 + self.d6  # ~1.477m
        
        # Minimum reach (telescopic at minimum)
        min_reach = abs(self.a2 + self.a3 - (self.d4_min + self.d5 + self.d6))  # depends on configuration
        
        # Height limits
        max_height = self.d1 + max_reach
        min_height = self.d1 - max_reach
        
        return {
            'max_reach': max_reach,
            'min_reach': min_reach, 
            'max_height': max_height,
            'min_height': min_height
        }

def test_robot():
    """Test the robot kinematics with sample configurations"""
    robot = RobotKinematics()
    
    print("=== 5-DOF Robot Forward Kinematics Test ===\n")
    
    # Test configurations
    test_configs = [
        # [θ1, θ2, θ3, d4, θ5, θ6] - angles in radians, distances in meters
        [0, 0, 0, 0.3, 0, 0],           # Home position
        [np.pi/4, np.pi/6, -np.pi/6, 0.4, np.pi/4, np.pi/2],  # General pose
        [np.pi/2, np.pi/2, 0, 0.647, 0, 0],        # Extended reach
        [0, -np.pi/2, np.pi/2, 0.282, -np.pi/2, np.pi],  # Folded configuration
    ]
    
    config_names = ["Home Position", "General Pose", "Extended Reach", "Folded Config"]
    
    for i, (config, name) in enumerate(zip(test_configs, config_names)):
        print(f"{i+1}. {name}")
        print(f"   Joints: θ1={config[0]:.3f}, θ2={config[1]:.3f}, θ3={config[2]:.3f}")
        print(f"           d4={config[3]:.3f}, θ5={config[4]:.3f}, θ6={config[5]:.3f}")
        
        T06, pos, rot, transforms = robot.forward_kinematics_numerical(config)
        
        print(f"   End-effector position: x={pos[0]:.3f}, y={pos[1]:.3f}, z={pos[2]:.3f} [m]")
        print(f"   Distance from base: {np.linalg.norm(pos[:2]):.3f} m")
        print(f"   Height: {pos[2]:.3f} m\n")
    
    # Workspace analysis
    limits = robot.get_workspace_limits()
    print("=== Workspace Limits ===")
    print(f"Maximum reach: {limits['max_reach']:.3f} m")
    print(f"Minimum reach: {limits['min_reach']:.3f} m") 
    print(f"Height range: {limits['min_height']:.3f} to {limits['max_height']:.3f} m")
    
    return robot

def visualize_robot_pose(robot, joint_config):
    """Improved visualization with better geometry"""
    T06, pos, rot, transforms = robot.forward_kinematics_numerical(joint_config)
    
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Calculate intermediate points for better link representation
    points = []
    T_current = np.eye(4)
    points.append(T_current[:3, 3])  # Base
    
    for i, T in enumerate(transforms):
        T_current = T_current @ T
        points.append(T_current[:3, 3])
    
    points = np.array(points)
    
    # Draw thicker, colored links
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown']
    for i in range(len(points)-1):
        ax.plot([points[i,0], points[i+1,0]], 
                [points[i,1], points[i+1,1]], 
                [points[i,2], points[i+1,2]], 
                linewidth=6, color=colors[i], label=f'Link {i+1}')
    
    # Draw joints as spheres
    for i, point in enumerate(points):
        ax.scatter(*point, s=200, color='black', alpha=0.8)
        ax.text(*point, f' J{i}', fontsize=12)
    
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)') 
    ax.set_zlabel('Z (m)')
    ax.legend()
    ax.set_title('6-DOF Robot Arm Visualization')
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.set_zlim([0, 1.5])
    
    plt.show()

if __name__ == "__main__":
    # Test the robot
    robot = test_robot()
    
    # Visualize a sample configuration
    sample_config = [np.pi/4, np.pi/6, -np.pi/6, 0.4, np.pi/4, np.pi/2]
    print(f"\nVisualizing robot configuration: {sample_config}")
    visualize_robot_pose(robot, sample_config)