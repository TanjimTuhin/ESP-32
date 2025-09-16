#!/usr/bin/env python3
"""
ESP32 IoT Control System - Complete GUI Client
- Potentiometer visualization with circular gauge
- Working servo control via slider/buttons
- LED control and button status display
- Real-time status updates
"""

import socket
import json
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import math
import os

CONFIG_FILE = "last_ip.txt"


class ESP32Client:
    def __init__(self, host, port=8080, auth_password="IoTDevice2024"):
        self.host = host
        self.port = port
        self.auth_password = auth_password
        self.socket = None
        self.authenticated = False
        self.running = False
        self.latest_status = {}
        self.lock = threading.Lock()

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            print(f"Connected to ESP32 at {self.host}:{self.port}")
            self.receive_message()  # read auth challenge
            return True
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect: {e}")
            return False

    def authenticate(self):
        try:
            self.send_message({"command": "auth", "password": self.auth_password})
            time.sleep(0.5)
            response = self.receive_message()
            if response and response.get("status") == "success":
                self.authenticated = True
                print("Authentication successful")
                return True
            else:
                messagebox.showerror("Auth Failed", str(response))
                return False
        except Exception as e:
            messagebox.showerror("Auth Error", str(e))
            return False

    def send_message(self, message):
        try:
            if self.socket:
                self.socket.send((json.dumps(message) + "\n").encode())
        except Exception as e:
            print(f"Send error: {e}")

    def receive_message(self):
        try:
            if self.socket:
                data = self.socket.recv(1024).decode()
                if not data:
                    return {}
                for line in data.strip().splitlines():
                    try:
                        return json.loads(line)
                    except:
                        continue
        except Exception as e:
            print(f"Receive error: {e}")
            return {}
        return {}

    def start_monitoring(self, update_callback):
        self.running = True
        threading.Thread(target=self._monitor_loop, args=(update_callback,), daemon=True).start()
        threading.Thread(target=self._keep_alive, daemon=True).start()

    def _monitor_loop(self, update_callback):
        buffer = ""
        while self.running:
            try:
                if not self.socket:
                    break
                data = self.socket.recv(1024).decode()
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    try:
                        msg = json.loads(line)
                        if msg.get("type") == "status":
                            with self.lock:
                                self.latest_status = msg
                            update_callback(msg)
                        else:
                            print("Server:", msg)
                    except Exception as e:
                        print(f"JSON parse error: {e}")
                        continue
            except Exception as e:
                print("Lost connection:", e)
                break

    def _keep_alive(self):
        while self.running and self.authenticated:
            time.sleep(25)
            self.ping()

    def control_led(self, led_number, state):
        self.send_message({"command": "set_led", "led": led_number, "state": state})
        time.sleep(0.1)
        self.get_status()

    def control_all_leds(self, state):
        self.send_message({"command": "set_all_leds", "state": state})
        time.sleep(0.1)
        self.get_status()

    def control_servo(self, angle):
        self.send_message({"command": "set_servo", "angle": angle})
        time.sleep(0.1)
        self.get_status()

    def toggle_led_sequence(self):
        if not self.authenticated:
            return
        # Note: The server-side will handle this when buttons are pressed
        # This is just for manual triggering from GUI
        for i in range(1, 6):
            self.control_led(i, True)
            time.sleep(0.2)
        time.sleep(1.0)
        for i in range(1, 6):
            self.control_led(i, False)
            time.sleep(0.2)

    def get_status(self):
        self.send_message({"command": "get_status"})

    def ping(self):
        self.send_message({"command": "ping"})

    def close(self):
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None


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


class ESP32GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 IoT Control System - Potentiometer Controlled Servo")
        self.root.geometry("700x800")
        self.root.resizable(False, False)

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

    def load_last_ip(self):
        """Load the last used IP address from config file"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    return f.read().strip()
        except:
            pass
        return "192.168.1.100"  # Default IP

    def save_last_ip(self, ip):
        """Save the IP address to config file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                f.write(ip)
        except:
            pass

    def create_connection_panel(self):
        conn_frame = ttk.Frame(self.root)
        conn_frame.pack(padx=10, pady=5, fill="x")

        ttk.Label(conn_frame, text="IP:").pack(side="left")
        self.ip_entry = ttk.Entry(conn_frame, width=15)
        self.ip_entry.pack(side="left", padx=5)
        self.ip_entry.insert(0, self.load_last_ip())

        ttk.Label(conn_frame, text="Port:").pack(side="left")
        self.port_entry = ttk.Entry(conn_frame, width=6)
        self.port_entry.pack(side="left", padx=5)
        self.port_entry.insert(0, "8080")

        ttk.Label(conn_frame, text="Password:").pack(side="left")
        self.pass_entry = ttk.Entry(conn_frame, width=15, show="*")
        self.pass_entry.pack(side="left", padx=5)
        self.pass_entry.insert(0, "IoTDevice2024")

        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_to_esp32)
        self.connect_btn.pack(side="left", padx=5)

        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", command=self.disconnect_from_esp32, state="disabled")
        self.disconnect_btn.pack(side="left", padx=5)

        self.status_label = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.status_label.pack(side="right")

    def create_led_control_panel(self):
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
        if self.connected:
            return

        host = self.ip_entry.get().strip()
        port = int(self.port_entry.get().strip())
        password = self.pass_entry.get().strip()

        if not host or not password:
            messagebox.showerror("Error", "Please enter IP and password")
            return

        self.client = ESP32Client(host, port, password)
        
        if self.client.connect():
            if self.client.authenticate():
                self.connected = True
                self.save_last_ip(host)
                
                # Update GUI
                self.connect_btn.config(state="disabled")
                self.disconnect_btn.config(state="normal")
                self.status_label.config(text="Connected", foreground="green")
                
                # Start monitoring
                self.client.start_monitoring(self.on_status_update)
                
                # Request initial status
                self.client.get_status()
                
                self.log_message(f"Connected to ESP32 at {host}:{port}")
            else:
                self.client.close()
                self.client = None

    def disconnect_from_esp32(self):
        if not self.connected:
            return

        if self.client:
            self.client.close()
            self.client = None

        self.connected = False
        
        # Update GUI
        self.connect_btn.config(state="normal")
        self.disconnect_btn.config(state="disabled")
        self.status_label.config(text="Disconnected", foreground="red")
        
        self.log_message("Disconnected from ESP32")

    def on_status_update(self, status):
        """Handle incoming status updates from ESP32"""
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
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to ESP32 first")
            return

        state = self.led_vars[led_number-1].get()
        self.client.control_led(led_number, state)
        self.log_message(f"LED {led_number} {'ON' if state else 'OFF'}")

    def control_all_leds(self, state):
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to ESP32 first")
            return

        self.client.control_all_leds(state)
        self.log_message(f"All LEDs {'ON' if state else 'OFF'}")

    def trigger_led_sequence(self):
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to ESP32 first")
            return

        self.log_message("Triggering LED sequence...")
        threading.Thread(target=self.client.toggle_led_sequence, daemon=True).start()

    def on_servo_scale_change(self, value):
        if self.updating_servo_controls:
            return
            
        angle = int(float(value))
        self.servo_value_label.config(text=f"{angle}°")

    def set_servo_angle(self, angle):
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
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to ESP32 first")
            return

        self.client.get_status()
        self.log_message("Status requested")

    def ping_server(self):
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to ESP32 first")
            return

        self.client.ping()
        self.log_message("Ping sent")

    def clear_status(self):
        self.status_text.delete(1.0, tk.END)

    def log_message(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)

    def on_closing(self):
        if self.connected:
            self.disconnect_from_esp32()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = ESP32GUI(root)
    
    # Handle window close event
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    main()