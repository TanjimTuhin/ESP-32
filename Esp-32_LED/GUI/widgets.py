"""
Custom widgets for ESP32 IoT Control System
"""

import tkinter as tk
import math

class PotentiometerGaugeWidget(tk.Canvas):
    """Custom widget for potentiometer visualization with circular gauge"""
    
    def __init__(self, parent, width=200, height=200):
        super().__init__(parent, width=width, height=height, bg='white', highlightthickness=1)
        self.width = width
        self.height = height
        self.center_x = width // 2
        self.center_y = height // 2
        self.radius = min(width, height) // 2 - 20
        self.value = 50  # Current percentage (0-100)
        
        self.draw_gauge()
    
    def draw_gauge(self):
        """Draw the gauge background and markings"""
        self.delete("all")
        
        # Draw outer circle
        self.create_oval(
            self.center_x - self.radius, self.center_y - self.radius,
            self.center_x + self.radius, self.center_y + self.radius,
            outline='black', width=3
        )
        
        # Draw inner circle (background)
        inner_radius = self.radius - 15
        self.create_oval(
            self.center_x - inner_radius, self.center_y - inner_radius,
            self.center_x + inner_radius, self.center_y + inner_radius,
            outline='lightgray', width=1
        )
        
        # Draw percentage markings
        for percent in [0, 25, 50, 75, 100]:
            angle = math.radians(270 + (percent / 100.0) * 360)  # Start from top, go clockwise
            
            outer_x = self.center_x + (self.radius - 5) * math.cos(angle)
            outer_y = self.center_y + (self.radius - 5) * math.sin(angle)
            inner_x = self.center_x + (self.radius - 15) * math.cos(angle)
            inner_y = self.center_y + (self.radius - 15) * math.sin(angle)
            
            self.create_line(outer_x, outer_y, inner_x, inner_y, fill='black', width=2)
            
            label_x = self.center_x + (self.radius - 25) * math.cos(angle)
            label_y = self.center_y + (self.radius - 25) * math.sin(angle)
            self.create_text(label_x, label_y, text=f"{percent}%", font=('Arial', 8))
        
        # Draw value indicator
        self.draw_indicator()
        
        # Draw center circle
        self.create_oval(
            self.center_x - 5, self.center_y - 5,
            self.center_x + 5, self.center_y + 5,
            fill='darkblue', outline='darkblue'
        )
        
        # Draw current value text
        self.create_text(
            self.center_x, self.center_y + 30,
            text=f"{self.value}%", font=('Arial', 14, 'bold'),
            tags='value_text'
        )
    
    def draw_indicator(self):
        """Draw the indicator needle based on current value"""
        # Calculate angle based on percentage (0% = top, 100% = full circle)
        angle = math.radians(270 + (self.value / 100.0) * 360)
        
        indicator_x = self.center_x + (self.radius - 20) * math.cos(angle)
        indicator_y = self.center_y + (self.radius - 20) * math.sin(angle)
        
        self.delete('indicator')
        
        # Draw indicator line
        self.create_line(
            self.center_x, self.center_y, indicator_x, indicator_y,
            fill='red', width=4, tags='indicator'
        )
        
        # Draw indicator dot
        self.create_oval(
            indicator_x - 4, indicator_y - 4, indicator_x + 4, indicator_y + 4,
            fill='red', outline='darkred', tags='indicator'
        )
    
    def set_value(self, value):
        """Set percentage value and redraw indicator"""
        self.value = max(0, min(100, value))
        self.draw_indicator()
        
        # Update text
        self.delete('value_text')
        self.create_text(
            self.center_x, self.center_y + 30,
            text=f"{self.value}%", font=('Arial', 14, 'bold'),
            tags='value_text'
        )