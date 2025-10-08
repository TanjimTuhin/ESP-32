"""
Main GUI for ESP32 IoT Control System
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time

from connection import ESP32Client
from widgets import PotentiometerGaugeWidget
from config import load_config, save_config

class ESP32GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 IoT Control System - Potentiometer Controlled Servo")
        
        # Load configuration
        self.config = load_config()
        self.root.geometry(self.config.get("window_geometry", "700x800"))
        self.root.resizable(False, False)

        # Initialize client
        self.client = None
        self.connected = False
        self.current_servo_angle = 90
        self.updating_servo_controls = False

        # Create all GUI panels
        self.create_connection_panel()
        self.create_led_control_panel()
        self.create_potentiometer_panel()
        self.create_servo_control_panel()
        self.create_button_panel()
        self.create_status_panel()

    def create_connection_panel(self):
        """Create connection control panel"""
        conn_frame = ttk.Frame(self.root)
        conn_frame.pack(padx=10, pady=5, fill="x")

        ttk.Label(conn_frame, text="IP:").pack(side="left")
        self.ip_entry = ttk.Entry(conn_frame, width=15)
        self.ip_entry.pack(side="left", padx=5)
        self.ip_entry.insert(0, self.config.get("host", "192.168.1.100"))

        ttk.Label(conn_frame, text="Port:").pack(side="left")
        self.port_entry = ttk.Entry(conn_frame, width=6)
        self.port_entry.pack(side="left", padx=5)
        self.port_entry.insert(0, str(self.config.get("port", 8080)))

        ttk.Label(conn_frame, text="Password:").pack(side="left")
        self.pass_entry = ttk.Entry(conn_frame, width=15, show="*")
        self.pass_entry.pack(side="left", padx=5)
        self.pass_entry.insert(0, self.config.get("password", "IoTDevice2024"))

        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_to_esp32)
        self.connect_btn.pack(side="left", padx=5)

        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", command=self.disconnect_from_esp32, state="disabled")
        self.disconnect_btn.pack(side="left", padx=5)

        self.status_label = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.status_label.pack(side="right")

    def create_led_control_panel(self):
        """Create LED control panel"""
        led_frame = ttk.LabelFrame(self.root, text="LED Control")
        led_frame.pack(padx=10, pady=5, fill="x")

        # Individual LED controls
        self.led_vars = []
        self.led_buttons = []
        
        individual_frame = ttk.Frame(led_frame)
        individual_frame.pack(pady=5)
        
        for i in range(5):
            var = tk.BooleanVar()
            self.led_vars.append(var)
            
            btn = ttk.Checkbutton(
                individual_frame, 
                text=f"LED {i+1}", 
                variable=var,
                command=lambda idx=i: self.toggle_led(idx+1)
            )
            btn.pack(side="left", padx=10)
            self.led_buttons.append(btn)

        # All LEDs control
        all_frame = ttk.Frame(led_frame)
        all_frame.pack(pady=5)

        ttk.Button(all_frame, text="All ON", command=lambda: self.control_all_leds(True)).pack(side="left", padx=5)
        ttk.Button(all_frame, text="All OFF", command=lambda: self.control_all_leds(False)).pack(side="left", padx=5)
        ttk.Button(all_frame, text="LED Sequence", command=self.trigger_led_sequence).pack(side="left", padx=5)

    def create_potentiometer_panel(self):
        """Create potentiometer display panel"""
        pot_frame = ttk.LabelFrame(self.root, text="Potentiometer Status (Auto-Controls Servo)")
        pot_frame.pack(padx=10, pady=5, fill="x")

        # Create gauge widget
        gauge_frame = ttk.Frame(pot_frame)
        gauge_frame.pack(pady=10)

        self.pot_gauge = PotentiometerGaugeWidget(gauge_frame, width=220, height=220)
        self.pot_gauge.pack(side="left", padx=10)

        # Potentiometer info
        info_frame = ttk.Frame(gauge_frame)
        info_frame.pack(side="left", padx=20, fill="both", expand=True)

        ttk.Label(info_frame, text="Potentiometer Status:", font=('Arial', 12, 'bold')).pack(anchor="w", pady=5)
        
        self.pot_raw_label = ttk.Label(info_frame, text="Raw Value: --")
        self.pot_raw_label.pack(anchor="w")
        
        self.pot_voltage_label = ttk.Label(info_frame, text="Voltage: --V")
        self.pot_voltage_label.pack(anchor="w")
        
        self.pot_percent_label = ttk.Label(info_frame, text="Percentage: --%")
        self.pot_percent_label.pack(anchor="w")

        ttk.Separator(info_frame, orient="horizontal").pack(fill="x", pady=10)
        
        ttk.Label(info_frame, text="Servo Status:", font=('Arial', 12, 'bold')).pack(anchor="w", pady=5)
        
        self.servo_angle_label = ttk.Label(info_frame, text="Current Angle: --°")
        self.servo_angle_label.pack(anchor="w")

        ttk.Label(info_frame, text="Note: Potentiometer automatically\ncontrols servo position", 
                 font=('Arial', 9), foreground="blue").pack(anchor="w", pady=10)

    def create_servo_control_panel(self):
        """Create servo control panel"""
        servo_frame = ttk.LabelFrame(self.root, text="Manual Servo Control (Temporary Override)")
        servo_frame.pack(padx=10, pady=5, fill="x")

        control_frame = ttk.Frame(servo_frame)
        control_frame.pack(pady=10)

        # Servo slider
        ttk.Label(control_frame, text="Angle:").pack(side="left")
        
        self.servo_var = tk.IntVar(value=90)
        self.servo_scale = ttk.Scale(
            control_frame, 
            from_=0, to=180, 
            variable=self.servo_var, 
            orient="horizontal", 
            length=300,
            command=self.on_servo_scale_change
        )
        self.servo_scale.pack(side="left", padx=10)

        self.servo_value_label = ttk.Label(control_frame, text="90°")
        self.servo_value_label.pack(side="left", padx=5)

        # Quick angle buttons
        button_frame = ttk.Frame(servo_frame)
        button_frame.pack(pady=5)

        angles = [0, 45, 90, 135, 180]
        for angle in angles:
            ttk.Button(
                button_frame, 
                text=f"{angle}°", 
                command=lambda a=angle: self.set_servo_angle(a)
            ).pack(side="left", padx=5)

        # Warning label
        ttk.Label(servo_frame, text="Note: Manual control is temporary - potentiometer will take over again", 
                 font=('Arial', 9), foreground="orange").pack(pady=5)

    def create_button_panel(self):
        """Create button status panel"""
        btn_frame = ttk.LabelFrame(self.root, text="Hardware Button Status")
        btn_frame.pack(padx=10, pady=5, fill="x")

        self.button_labels = []
        button_grid = ttk.Frame(btn_frame)
        button_grid.pack(pady=10)

        for i in range(5):
            label = ttk.Label(button_grid, text=f"Button {i+1}: Released", 
                            relief="raised", padding=5)
            label.grid(row=0, column=i, padx=5, pady=5)
            self.button_labels.append(label)

        ttk.Label(btn_frame, text="Press hardware buttons to trigger LED sequence", 
                 font=('Arial', 9), foreground="blue").pack(pady=5)

    def create_status_panel(self):
        """Create status display panel"""
        status_frame = ttk.LabelFrame(self.root, text="System Status")
        status_frame.pack(padx=10, pady=5, fill="both", expand=True)

        # Create text widget with scrollbar
        text_frame = ttk.Frame(status_frame)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.status_text = tk.Text(text_frame, height=8, font=('Courier', 9))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)

        self.status_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Control buttons
        control_frame = ttk.Frame(status_frame)
        control_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(control_frame, text="Get Status", command=self.request_status).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Clear Log", command=self.clear_status).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Ping", command=self.ping_server).pack(side="left", padx=5)

    def connect_to_esp32(self):
        """Connect to ESP32 device"""
        if self.connected:
            return

        host = self.ip_entry.get().strip()
        port = int(self.port_entry.get().strip())
        password = self.pass_entry.get().strip()

        if not host or not password:
            messagebox.showerror("Error", "Please enter IP and password")
            return

        # Save configuration
        self.config.update({
            "host": host,
            "port": port,
            "password": password
        })
        save_config(self.config)

        self.client = ESP32Client(host, port, password)
        
        # Register callbacks
        self.client.register_connection_callback(self.on_connection_event)
        self.client.register_status_callback(self.on_status_update)
        
        if self.client.connect():
            if self.client.authenticate():
                self.connected = True
                
                # Update GUI
                self.connect_btn.config(state="disabled")
                self.disconnect_btn.config(state="normal")
                
                # Start monitoring
                self.client.start_monitoring()
                
                # Request initial status
                self.client.get_status()
                
                self.log_message(f"Connected to ESP32 at {host}:{port}")
            else:
                self.client.close()
                self.client = None

    def disconnect_from_esp32(self):
        """Disconnect from ESP32 device"""
        if not self.connected:
            return

        if self.client:
            self.client.close()
            self.client = None

        self.connected = False
        
        # Update GUI
        self.connect_btn.config(state="normal")
        self.disconnect_btn.config(state="disabled")
        
        self.log_message("Disconnected from ESP32")

    def on_connection_event(self, connected, message):
        """Handle connection events from ESP32Client"""
        self.root.after(0, self._update_connection_status, connected, message)

    def _update_connection_status(self, connected, message):
        """Update connection status in GUI (runs in main thread)"""
        if connected:
            self.status_label.config(text="Connected", foreground="green")
        else:
            self.status_label.config(text="Disconnected", foreground="red")
            if message:
                self.log_message(message)

    def on_status_update(self, status):
        """Handle status updates from ESP32"""
        self.root.after(0, self._update_gui_from_status, status)

    def _update_gui_from_status(self, status):
        """Update GUI elements based on received status (runs in main thread)"""
        try:
            # Update LED states
            if "leds" in status:
                for i, led in enumerate(status["leds"]):
                    if i < len(self.led_vars):
                        self.led_vars[i].set(led.get("state", False))

            # Update potentiometer display
            if "potentiometer" in status:
                pot_data = status["potentiometer"]
                
                # Update gauge
                percent = pot_data.get("percent", 0)
                self.pot_gauge.set_value(percent)
                
                # Update labels
                self.pot_raw_label.config(text=f"Raw Value: {pot_data.get('raw', '--')}")
                self.pot_voltage_label.config(text=f"Voltage: {pot_data.get('voltage', '--'):.2f}V")
                self.pot_percent_label.config(text=f"Percentage: {percent}%")

            # Update servo angle
            if "servo" in status:
                angle = status["servo"].get("angle", 90)
                self.current_servo_angle = angle
                self.servo_angle_label.config(text=f"Current Angle: {angle}°")
                
                # Update servo controls (but don't trigger callbacks)
                if not self.updating_servo_controls:
                    self.updating_servo_controls = True
                    self.servo_var.set(angle)
                    self.servo_value_label.config(text=f"{angle}°")
                    self.updating_servo_controls = False

            # Update button states
            if "buttons" in status:
                for i, btn in enumerate(status["buttons"]):
                    if i < len(self.button_labels):
                        pressed = btn.get("pressed", False)
                        state_text = "Pressed" if pressed else "Released"
                        color = "lightcoral" if pressed else "lightgreen"
                        self.button_labels[i].config(
                            text=f"Button {i+1}: {state_text}",
                            background=color
                        )

        except Exception as e:
            print(f"GUI update error: {e}")

    def toggle_led(self, led_number):
        """Toggle an individual LED"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to ESP32 first")
            return

        state = self.led_vars[led_number-1].get()
        self.client.control_led(led_number, state)
        self.log_message(f"LED {led_number} {'ON' if state else 'OFF'}")

    def control_all_leds(self, state):
        """Control all LEDs at once"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to ESP32 first")
            return

        self.client.control_all_leds(state)
        self.log_message(f"All LEDs {'ON' if state else 'OFF'}")

    def trigger_led_sequence(self):
        """Trigger LED sequence"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to ESP32 first")
            return

        self.log_message("Triggering LED sequence...")
        # Note: This would need to be implemented on the ESP32 side

    def on_servo_scale_change(self, value):
        """Handle servo scale change events"""
        if self.updating_servo_controls:
            return
            
        angle = int(float(value))
        self.servo_value_label.config(text=f"{angle}°")

    def set_servo_angle(self, angle):
        """Set servo to a specific angle"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to ESP32 first")
            return

        self.updating_servo_controls = True
        self.servo_var.set(angle)
        self.servo_value_label.config(text=f"{angle}°")
        self.updating_servo_controls = False

        self.client.control_servo(angle)
        self.log_message(f"Servo set to {angle}° (manual override)")

    def request_status(self):
        """Request status update from ESP32"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to ESP32 first")
            return

        self.client.get_status()
        self.log_message("Status requested")

    def ping_server(self):
        """Ping the ESP32 server"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to ESP32 first")
            return

        self.client.ping()
        self.log_message("Ping sent")

    def clear_status(self):
        """Clear the status log"""
        self.status_text.delete(1.0, tk.END)

    def log_message(self, message):
        """Add a message to the status log"""
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)

    def on_closing(self):
        """Handle application closing"""
        if self.connected:
            self.disconnect_from_esp32()
        
        # Save window geometry
        self.config["window_geometry"] = self.root.geometry()
        save_config(self.config)
        
        self.root.destroy()