# First install: pip install roboticstoolbox-python
from roboticstoolbox import DHRobot, RevoluteDH, PrismaticDH
import roboticstoolbox as rtb
import numpy as np

# Create the robot using DH parameters
robot = DHRobot([
    RevoluteDH(d=0.1, a=0, alpha=np.pi/2),    # Joint 1
    RevoluteDH(d=0, a=0.338, alpha=0),        # Joint 2  
    RevoluteDH(d=0, a=0.171, alpha=0),        # Joint 3
    PrismaticDH(theta=0, a=0, alpha=np.pi/2), # Joint 4
    RevoluteDH(d=0.095, a=0, alpha=-np.pi/2), # Joint 5
    RevoluteDH(d=0.226, a=0, alpha=0)         # Joint 6
], name='6DOF-Robot')

# Test configuration
q = [0, np.pi/4, -np.pi/6, 0.4, np.pi/4, 0]

# This will show a proper 3D robot model!
robot.plot(q, backend='pyplot', shadow=True)