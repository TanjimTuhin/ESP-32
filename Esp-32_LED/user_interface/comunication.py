#!/usr/bin/env python3
"""
ESP32 IoT Control System - Enhanced GUI Client with Visual Servo Control
"""

import socket, json, threading, time, tkinter as tk
from tkinter import ttk, messagebox
import math

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
            self.socket.send((json.dumps(message) + "\n").encode())
        except:
            pass

    def receive_message(self):
        try:
            data = self.socket.recv(1024).decode()
            if not data:
                return {}
            for line in data.strip().splitlines():
                try:
                    return json.loads(line)
                except:
                    continue
        except:
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
                    except:
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
        self.get_status()

    def control_all_leds(self, state):
        self.send_message({"command": "set_all_leds", "state": state})
        self.get_status()

    def control_servo(self, angle):
        self.send_message({"command": "set_servo", "angle": angle})
        self.get_status()

    def toggle_led_sequence(self):
        if not self.authenticated:
            return
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
            self.socket.close()


class ServoGaugeWidget(tk.Canvas):
    """Custom widget for visual servo control with circular gauge"""
    
    def __init__(self, parent, width=200, height=200, callback=None):
        super().__init__(parent, width=width, height=height, bg='white', highlightthickness=1)
        self.width = width
        self.height = height
        self.center_x = width // 2
        self.center_y = height // 2
        self.radius = min(width, height) // 2 - 20
        self.angle = 90  # Current angle (0-180)
        self.callback = callback
        self.dragging = False
        
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        
        self.draw_gauge()
    
    def draw_gauge(self):
        self.delete("all")
        
        # Draw arc background (semicircle from 0 to 180 degrees)
        arc_start = 0
        arc_extent = 180
        
        # Outer arc
        self.create_arc(
            self.center_x - self.radius, self.center_y - self.radius,
            self.center_x + self.radius, self.center_y + self.radius,
            start=arc_start, extent=arc_extent, outline='black', width=3,
            style='arc'
        )
        
        # Inner arc for filled area
        self.create_arc(
            self.center_x - self.radius + 10, self.center_y - self.radius + 10,
            self.center_x + self.radius - 10, self.center_y + self.radius - 10,
            start=arc_start, extent=arc_extent, outline='lightgray', width=1,
            style='arc'
        )
        
        # Draw angle markings
        for angle in [0, 30, 45, 60, 90, 120, 135, 150, 180]:
            canvas_angle = math.radians(180 - angle)
            
            outer_x = self.center_x + (self.radius - 5) * math.cos(canvas_angle)
            outer_y = self.center_y - (self.radius - 5) * math.sin(canvas_angle)
            inner_x = self.center_x + (self.radius - 15) * math.cos(canvas_angle)
            inner_y = self.center_y - (self.radius - 15) * math.sin(canvas_angle)
            
            self.create_line(outer_x, outer_y, inner_x, inner_y, fill='black', width=2)
            
            label_x = self.center_x + (self.radius - 25) * math.cos(canvas_angle)
            label_y = self.center_y - (self.radius - 25) * math.sin(canvas_angle)
            self.create_text(label_x, label_y, text=str(angle), font=('Arial', 8))
        
        # Draw pointer
        self.draw_pointer()
        
        # Draw center circle
        self.create_oval(
            self.center_x - 5, self.center_y - 5,
            self.center_x + 5, self.center_y + 5,
            fill='black', outline='black'
        )
        
        # Draw current angle text
        self.create_text(
            self.center_x, self.center_y + 30,
            text=f"{self.angle}°", font=('Arial', 14, 'bold'),
            tags='angle_text'
        )
    
    def draw_pointer(self):
        canvas_angle = math.radians(180 - self.angle)
        
        pointer_x = self.center_x + (self.radius - 20) * math.cos(canvas_angle)
        pointer_y = self.center_y - (self.radius - 20) * math.sin(canvas_angle)
        
        self.delete('pointer')
        
        self.create_line(
            self.center_x, self.center_y, pointer_x, pointer_y,
            fill='red', width=3, tags='pointer'
        )
        
        self.create_oval(
            pointer_x - 3, pointer_y - 3, pointer_x + 3, pointer_y + 3,
            fill='red', outline='red', tags='pointer'
        )
    
    def on_click(self, event):
        self.dragging = True
        self.update_angle_from_mouse(event.x, event.y)
    
    def on_drag(self, event):
        if self.dragging:
            self.update_angle_from_mouse(event.x, event.y)
    
    def on_release(self, event):
        self.dragging = False
    
    def update_angle_from_mouse(self, x, y):
        dx = x - self.center_x
        dy = self.center_y - y
        
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        if angle_deg < 0:
            angle_deg = 0
        elif angle_deg > 180:
            angle_deg = 180
        
        self.set_angle(int(angle_deg))
        
        if self.callback:
            self.callback(self.angle)
    
    def set_angle(self, angle):
        """Set angle and redraw pointer"""
        self.angle = max(0, min(180, angle))
        self.draw_pointer()
        
        self.delete('angle_text')
        self.create_text(
            self.center_x, self.center_y + 30,
            text=f"{self.angle}°", font=('Arial', 14, 'bold'),
            tags='angle_text'
        )


class ESP32GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 IoT Control System - Enhanced Servo Control")
        self.root.geometry("650x760")

        self.client = None
        self.connected = False
        self.current_servo_angle = 90
        self.updating_controls = False  # Flag to prevent circular updates

        # Connection panel
        conn_frame = ttk.Frame(root)
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

        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_to_esp)
        self.connect_btn.pack(side="left", padx=5)

        self.status_label = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.status_label.pack(side="left", padx=10)

        # LED control
        led_frame = ttk.LabelFrame(root, text="LED Control")
        led_frame.pack(padx=10, pady=5, fill="x")

        self.led_buttons = []
        for i in range(1, 6):
            var = tk.BooleanVar()
            chk = tk.Checkbutton(
                led_frame, text=f"LED {i}", variable=var,
                command=lambda i=i, v=var: self.client.control_led(i, v.get()) if self.client else None
            )
            chk.pack(side="left", padx=5, pady=5)
            self.led_buttons.append(var)

        ttk.Button(led_frame, text="All ON", command=lambda: self.client.control_all_leds(True) if self.client else None).pack(side="left", padx=5)
        ttk.Button(led_frame, text="All OFF", command=lambda: self.client.control_all_leds(False) if self.client else None).pack(side="left", padx=5)
        ttk.Button(
            led_frame, text="Toggle Sequence",
            command=lambda: threading.Thread(target=self.client.toggle_led_sequence, daemon=True).start() if self.client else None
        ).pack(side="left", padx=5)

        # Enhanced Servo control
        servo_frame = ttk.LabelFrame(root, text="Servo Control (0-180°)")
        servo_frame.pack(padx=10, pady=5, fill="x")
        
        servo_container = ttk.Frame(servo_frame)
        servo_container.pack(fill="x", padx=5, pady=5)
        
        # Left side - Visual gauge
        gauge_frame = ttk.Frame(servo_container)
        gauge_frame.pack(side="left", padx=10)
        
        ttk.Label(gauge_frame, text="Visual Control", font=('Arial', 10, 'bold')).pack()
        self.servo_gauge = ServoGaugeWidget(gauge_frame, 200, 200, self.on_gauge_change)
        self.servo_gauge.pack(pady=5)
        
        # Right side - Controls
        controls_frame = ttk.Frame(servo_container)
        controls_frame.pack(side="left", fill="x", expand=True, padx=20)
        
        # Input controls row
        input_frame = ttk.Frame(controls_frame)
        input_frame.pack(pady=10)
        
        ttk.Label(input_frame, text="Angle Control:", font=('Arial', 10, 'bold')).pack(anchor="w")
        
        angle_control_frame = ttk.Frame(input_frame)
        angle_control_frame.pack(pady=5)
        
        # Decrease button
        self.decrease_btn = ttk.Button(angle_control_frame, text="−", width=3, 
                                     command=self.decrease_angle)
        self.decrease_btn.pack(side="left", padx=2)
        
        # Angle entry
        self.servo_entry = ttk.Entry(angle_control_frame, width=5, justify="center")
        self.servo_entry.insert(0, "90")
        self.servo_entry.pack(side="left", padx=2)
        self.servo_entry.bind("<Return>", self.on_entry_change)
        self.servo_entry.bind("<FocusOut>", self.on_entry_change)
        
        # Increase button
        self.increase_btn = ttk.Button(angle_control_frame, text="+", width=3,
                                     command=self.increase_angle)
        self.increase_btn.pack(side="left", padx=2)
        
        # Set button
        ttk.Button(angle_control_frame, text="Set", command=self.set_servo_angle).pack(side="left", padx=5)
        
        # Preset angles
        preset_frame = ttk.Frame(controls_frame)
        preset_frame.pack(pady=10)
        
        ttk.Label(preset_frame, text="Preset Angles:", font=('Arial', 10, 'bold')).pack(anchor="w")
        
        preset_buttons_frame = ttk.Frame(preset_frame)
        preset_buttons_frame.pack(pady=5)
        
        preset_angles = [0, 30, 45, 90, 120, 150, 180]
        for angle in preset_angles:
            btn = ttk.Button(preset_buttons_frame, text=f"{angle}°", width=5,
                           command=lambda a=angle: self.set_preset_angle(a))
            btn.pack(side="left", padx=1)
        
        # Slider for alternative control
        slider_frame = ttk.Frame(controls_frame)
        slider_frame.pack(fill="x", pady=10)
        
        ttk.Label(slider_frame, text="Slider Control:", font=('Arial', 10, 'bold')).pack(anchor="w")
        self.servo_slider = ttk.Scale(slider_frame, from_=0, to=180, orient="horizontal", 
                                    command=self.on_slider_change)
        self.servo_slider.set(90)
        self.servo_slider.pack(fill="x", pady=5)

        # Status area
        status_frame = ttk.LabelFrame(root, text="System Status")
        status_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.status_text = tk.Text(status_frame, height=8, state="disabled")
        scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        self.status_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def on_gauge_change(self, angle):
        """Called when gauge angle changes"""
        if self.updating_controls:
            return
        self.current_servo_angle = angle
        self.update_other_controls_from_gauge(angle)
        if self.client and self.connected:
            self.client.control_servo(angle)

    def on_slider_change(self, value):
        """Called when slider changes"""
        if self.updating_controls:
            return
        angle = int(float(value))
        self.current_servo_angle = angle
        self.update_other_controls_from_slider(angle)

    def on_entry_change(self, event=None):
        """Called when entry box changes"""
        if self.updating_controls:
            return
        try:
            angle = int(self.servo_entry.get())
            angle = max(0, min(180, angle))
            self.current_servo_angle = angle
            self.update_other_controls_from_entry(angle)
        except ValueError:
            self.servo_entry.delete(0, tk.END)
            self.servo_entry.insert(0, str(self.current_servo_angle))

    def decrease_angle(self):
        """Decrease angle by 1 degree"""
        new_angle = max(0, self.current_servo_angle - 1)
        self.current_servo_angle = new_angle
        self.update_all_angle_displays(new_angle)
        if self.client and self.connected:
            self.client.control_servo(new_angle)

    def increase_angle(self):
        """Increase angle by 1 degree"""
        new_angle = min(180, self.current_servo_angle + 1)
        self.current_servo_angle = new_angle
        self.update_all_angle_displays(new_angle)
        if self.client and self.connected:
            self.client.control_servo(new_angle)

    def set_preset_angle(self, angle):
        """Set servo to preset angle"""
        self.current_servo_angle = angle
        self.update_all_angle_displays(angle)
        if self.client and self.connected:
            self.client.control_servo(angle)

    def set_servo_angle(self):
        """Set servo angle from entry box"""
        try:
            angle = int(self.servo_entry.get())
            if angle < 0 or angle > 180:
                messagebox.showerror("Invalid Angle", "Angle must be between 0 and 180 degrees")
                return
            self.current_servo_angle = angle
            self.update_all_angle_displays(angle)
            if self.client and self.connected:
                self.client.control_servo(angle)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number")

    def update_all_angle_displays(self, angle):
        """Update all angle display elements"""
        self.updating_controls = True
        try:
            self.servo_gauge.set_angle(angle)
            self.servo_entry.delete(0, tk.END)
            self.servo_entry.insert(0, str(angle))
            self.servo_slider.set(angle)
        finally:
            self.updating_controls = False

    def update_other_controls_from_gauge(self, angle):
        """Update all controls except gauge"""
        self.updating_controls = True
        try:
            self.servo_entry.delete(0, tk.END)
            self.servo_entry.insert(0, str(angle))
            self.servo_slider.set(angle)
        finally:
            self.updating_controls = False

    def update_other_controls_from_slider(self, angle):
        """Update all controls except slider"""
        self.updating_controls = True
        try:
            self.servo_gauge.set_angle(angle)
            self.servo_entry.delete(0, tk.END)
            self.servo_entry.insert(0, str(angle))
        finally:
            self.updating_controls = False

    def update_other_controls_from_entry(self, angle):
        """Update all controls except entry"""
        self.updating_controls = True
        try:
            self.servo_gauge.set_angle(angle)
            self.servo_slider.set(angle)
        finally:
            self.updating_controls = False

    def connect_to_esp(self):
        if self.connected:
            self.client.close()
            self.client = None
            self.connected = False
            self.status_label.config(text="Disconnected", foreground="red")
            self.connect_btn.config(text="Connect")
            return

        ip = self.ip_entry.get().strip()
        port = int(self.port_entry.get().strip())
        password = self.pass_entry.get().strip()

        if not ip:
            ip = self.load_last_ip()
            self.ip_entry.insert(0, ip)

        self.save_last_ip(ip)
        self.client = ESP32Client(ip, port, password)

        if not self.client.connect():
            self.status_label.config(text="Disconnected", foreground="red")
            return
        if not self.client.authenticate():
            self.status_label.config(text="Disconnected", foreground="red")
            return

        self.client.start_monitoring(self.update_status)
        self.client.get_status()
        self.status_label.config(text="Connected", foreground="green")
        self.connect_btn.config(text="Disconnect")
        self.connected = True

    def update_status(self, status):
        self.status_text.config(state="normal")
        self.status_text.delete("1.0", tk.END)

        self.status_text.insert(tk.END, f"Timestamp: {status.get('timestamp')}\n\n")

        self.status_text.insert(tk.END, "LEDs:\n")
        for led in status.get("leds", []):
            state_text = "ON" if led['state'] else "OFF"
            self.status_text.insert(tk.END, f"  LED {led['id']}: {state_text}\n")
            self.led_buttons[led['id'] - 1].set(led['state'])

        self.status_text.insert(tk.END, "\nButtons:\n")
        for btn in status.get("buttons", []):
            status_text = "PRESSED" if btn['pressed'] else "released"
            self.status_text.insert(tk.END, f"  Button {btn['id']}: {status_text}\n")

        pot = status.get("potentiometer", {})
        self.status_text.insert(tk.END, "\nPotentiometer:\n")
        self.status_text.insert(tk.END, f"  Raw: {pot.get('raw', 0)}\n")
        self.status_text.insert(tk.END, f"  Voltage: {pot.get('voltage', 0):.2f} V\n")
        self.status_text.insert(tk.END, f"  Percent: {pot.get('percent', 0)} %\n")
        
        servo = status.get("servo", {})
        if servo:
            self.status_text.insert(tk.END, "\nServo:\n")
            self.status_text.insert(tk.END, f"  Angle: {servo.get('angle', 0)}°\n")
            servo_angle = servo.get('angle', 90)
            if servo_angle != self.current_servo_angle:
                self.current_servo_angle = servo_angle
                self.update_all_angle_displays(servo_angle)

        self.status_text.config(state="disabled")
        self.status_text.see(tk.END)

    def save_last_ip(self, ip):
        try:
            with open(CONFIG_FILE, "w") as f:
                f.write(ip)
        except:
            pass

    def load_last_ip(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                return f.read().strip()
        except:
            return ""


def main():
    root = tk.Tk()
    gui = ESP32GUI(root)
    
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_width()) // 2
    y = (root.winfo_screenheight() - root.winfo_height()) // 2
    root.geometry(f"+{x}+{y}")
    
    try:
        root.mainloop()
    finally:
        if gui.client:
            gui.client.close()


if __name__ == "__main__":
    main()