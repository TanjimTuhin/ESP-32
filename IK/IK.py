# analytic_2link.py
# Analytic IK for a 2-link planar arm + small matplotlib visualization
import numpy as np
import matplotlib.pyplot as plt

def wrap_to_pi(angle):
    return (angle + np.pi) % (2*np.pi) - np.pi

def analytic_ik_2link(x, y, l1, l2, tol=1e-9):
    r2 = x*x + y*y
    D = (r2 - l1*l1 - l2*l2) / (2*l1*l2)
    if D > 1 + tol or D < -1 - tol:
        return []  # unreachable
    D = max(-1.0, min(1.0, D))  # clamp numeric
    s = np.sqrt(max(0.0, 1 - D*D))
    # two possible theta2 (elbow up / down)
    theta2_a = np.arctan2(s, D)
    theta2_b = np.arctan2(-s, D)
    solutions = []
    for theta2 in (theta2_a, theta2_b):
        k1 = l1 + l2 * np.cos(theta2)
        k2 = l2 * np.sin(theta2)
        theta1 = np.arctan2(y, x) - np.arctan2(k2, k1)
        solutions.append((wrap_to_pi(theta1), wrap_to_pi(theta2)))
    # filter duplicates (if s ~ 0 both same)
    uniq = []
    for sol in solutions:
        if not any(np.allclose(sol, u, atol=1e-6) for u in uniq):
            uniq.append(sol)
    return uniq

def fk_2link(theta1, theta2, l1, l2):
    x1 = l1 * np.cos(theta1)
    y1 = l1 * np.sin(theta1)
    x2 = x1 + l2 * np.cos(theta1 + theta2)
    y2 = y1 + l2 * np.sin(theta1 + theta2)
    return (0,0), (x1,y1), (x2,y2)

if __name__ == "__main__":
    # How to use: adjust l1, l2 and target (x, y)
    l1, l2 = 1.0, 0.7
    targets = [(1.1, 0.2), (0.2, 0.9), (-0.9, 0.75)]  # last likely unreachable
    for x,y in targets:
        sols = analytic_ik_2link(x, y, l1, l2)
        print(f"\nTarget ({x:.3f}, {y:.3f}), solutions: {len(sols)}")
        if not sols:
            print(" Unreachable")
            continue
        for i,(t1,t2) in enumerate(sols):
            (o,p1,p2) = fk_2link(t1, t2, l1, l2)
            print(f" Solution {i+1}: theta1={np.degrees(t1):.2f}°, theta2={np.degrees(t2):.2f}°, FK-> ({p2[0]:.3f},{p2[1]:.3f})")
        # plot
        plt.figure()
        for t1,t2 in sols:
            o,p1,p2 = fk_2link(t1,t2,l1,l2)
            xs = [o[0], p1[0], p2[0]]
            ys = [o[1], p1[1], p2[1]]
            plt.plot(xs, ys, marker='o')
        plt.plot(x, y, 'rx', label='target')
        circle = plt.Circle((0,0), l1 + l2, color='k', fill=False, linestyle='--', alpha=0.3)
        plt.gca().add_patch(circle)
        plt.axis('equal')
        plt.legend()
        plt.title(f"Target ({x:.2f},{y:.2f})")
    plt.show()
