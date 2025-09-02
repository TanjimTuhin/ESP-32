#!/usr/bin/env python3
"""
ESP32 IoT Control System - GUI Client (with Toggle Sequence)
"""

import socket, json, threading, time, tkinter as tk
from tkinter import ttk, messagebox

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
            print(f"✓ Connected to ESP32 at {self.host}:{self.port}")
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
                print("✓ Authentication successful")
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
                print("✗ Lost connection:", e)
                break

    def _keep_alive(self):
        while self.running and self.authenticated:
            time.sleep(25)
            self.ping()

    def control_led(self, led_number, state):
        self.send_message({"command": "set_led", "led": led_number, "state": state})
        self.get_status()  # immediate refresh

    def control_all_leds(self, state):
        self.send_message({"command": "set_all_leds", "state": state})
        self.get_status()

    def toggle_led_sequence(self):
        """Turn LEDs on one by one, wait, then off one by one"""
        if not self.authenticated:
            return
        # Turn ON one by one
        for i in range(1, 6):
            self.control_led(i, True)
            time.sleep(0.2)

        time.sleep(1.0)  # hold all ON

        # Turn OFF one by one
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


# ---------------- GUI ---------------- #
class ESP32GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 IoT Control System")
        self.client = None
        self.connected = False

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

        ttk.Button(led_frame, text="All ON", command=lambda: self.client.control_all_leds(True)).pack(side="left", padx=5)
        ttk.Button(led_frame, text="All OFF", command=lambda: self.client.control_all_leds(False)).pack(side="left", padx=5)
        ttk.Button(
            led_frame, text="Toggle Sequence",
            command=lambda: threading.Thread(target=self.client.toggle_led_sequence, daemon=True).start()
        ).pack(side="left", padx=5)

        # Status area
        status_frame = ttk.LabelFrame(root, text="Status")
        status_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.status_text = tk.Text(status_frame, height=12, state="disabled")
        self.status_text.pack(fill="both", expand=True)

    def connect_to_esp(self):
        if self.connected:  # Disconnect mode
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
            self.status_text.insert(tk.END, f"  LED {led['id']}: {'ON' if led['state'] else 'OFF'}\n")
            self.led_buttons[led['id'] - 1].set(led['state'])

        self.status_text.insert(tk.END, "\nButtons:\n")
        for btn in status.get("buttons", []):
            self.status_text.insert(tk.END, f"  Button {btn['id']}: {'PRESSED' if btn['pressed'] else 'released'}\n")

        pot = status.get("potentiometer", {})
        self.status_text.insert(tk.END, "\nPotentiometer:\n")
        self.status_text.insert(tk.END, f"  Raw: {pot.get('raw', 0)}\n")
        self.status_text.insert(tk.END, f"  Voltage: {pot.get('voltage', 0):.2f} V\n")
        self.status_text.insert(tk.END, f"  Percent: {pot.get('percent', 0)} %\n")

        self.status_text.config(state="disabled")

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
    root.mainloop()
    if gui.client:
        gui.client.close()


if __name__ == "__main__":
    main()
