import tkinter as tk
from tkinter import ttk, messagebox
import socket
import json
import threading
import queue
import os
import sys

# --- Configuration ---
CONFIG_FILE = "esp32_connection.conf"
DEFAULT_IP = "192.168.1.100"
DEFAULT_PORT = 8080
AUTH_PASSWORD = "IoTDevice2024"

class ESP32ClientThread(threading.Thread):
    """
    Handles all network communication in a separate thread to prevent the GUI from freezing.
    """
    def __init__(self, host, port, gui_queue):
        super().__init__()
        self.host = host
        self.port = port
        self.gui_queue = gui_queue
        self.sock = None
        self.is_running = True
        self.is_authenticated = False

    def run(self):
        """Main loop for the network thread."""
        try:
            # Create and connect the socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5.0) # 5-second timeout for connection
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(1.0) # 1-second timeout for subsequent operations
            
            # Authenticate with the server
            self._send_command({"command": "auth", "password": AUTH_PASSWORD})

            # Listen for responses
            buffer = ""
            while self.is_running:
                try:
                    data = self.sock.recv(1024)
                    if not data:
                        # Server closed connection
                        self._report_disconnected()
                        break

                    buffer += data.decode('utf-8')
                    
                    # Process all complete JSON messages in the buffer
                    while '\n' in buffer:
                        message_str, buffer = buffer.split('\n', 1)
                        if message_str:
                            self._process_server_message(message_str)

                except socket.timeout:
                    # No data received, loop continues to check is_running
                    continue
                except Exception as e:
                    self._report_error(f"Receive error: {e}")
                    break

        except socket.timeout:
            self._report_error("Connection timed out. Check IP and server status.")
        except ConnectionRefusedError:
            self._report_error("Connection refused. Is the ESP32 server running?")
        except Exception as e:
            self._report_error(f"Connection failed: {e}")
        finally:
            self._report_disconnected()
            self.close()

    def _process_server_message(self, message_str):
        """Parses a JSON message from the server and acts on it."""
        try:
            message = json.loads(message_str)
            if message.get("status") == "success":
                if not self.is_authenticated:
                    self.is_authenticated = True
                    self.gui_queue.put({"status": "connected"})
            elif message.get("status") == "error":
                error_msg = message.get("message", "Unknown error from ESP32")
                self._report_error(f"ESP32 Error: {error_msg}")
        except json.JSONDecodeError:
            print(f"Received non-JSON message: {message_str}")

    def _send_command(self, command_dict):
        """Sends a JSON command to the ESP32."""
        if self.sock:
            try:
                message = json.dumps(command_dict) + "\n"
                self.sock.sendall(message.encode('utf-8'))
            except Exception as e:
                self._report_error(f"Send error: {e}")

    def send_servo_angle(self, angle):
        """Specifically sends the servo control command."""
        if self.is_authenticated:
            self._send_command({"command": "set_servo", "angle": angle})

    def _report_error(self, error_msg):
        self.gui_queue.put({"status": "error", "message": error_msg})

    def _report_disconnected(self):
        self.gui_queue.put({"status": "disconnected"})

    def close(self):
        """Stops the thread and closes the socket."""
        self.is_running = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except OSError:
                # Socket might already be closed
                pass
            self.sock = None
            self.is_authenticated = False


class ServoControllerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ESP32 Servo Control (Python)")
        self.geometry("450x200")
        self.resizable(False, False)

        self.client_thread = None
        self.gui_queue = queue.Queue()
        self.is_connected = False
        self.last_sent_angle = 90 # To avoid flooding the server

        self._create_widgets()
        self.load_last_connection_info()
        self.update_ui_state()
        
        # Start the queue checker
        self.after(100, self.process_queue)
        
        # Ensure client is disconnected on window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Connection Group ---
        conn_group = ttk.LabelFrame(main_frame, text="Connection", padding="10")
        conn_group.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(conn_group, text="IP:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.ip_var = tk.StringVar()
        self.ip_entry = ttk.Entry(conn_group, textvariable=self.ip_var, width=20)
        self.ip_entry.grid(row=0, column=1, padx=5)

        ttk.Label(conn_group, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.port_var = tk.StringVar(value=str(DEFAULT_PORT))
        self.port_entry = ttk.Entry(conn_group, textvariable=self.port_var, width=8)
        self.port_entry.grid(row=0, column=3, padx=5)

        self.connect_button = ttk.Button(conn_group, text="Connect", command=self.toggle_connection)
        self.connect_button.grid(row=0, column=4, padx=(10, 0))

        # --- Servo Control Group ---
        servo_group = ttk.LabelFrame(main_frame, text="Servo Control", padding="10")
        servo_group.pack(fill=tk.X, padx=5, pady=5)
        servo_group.grid_columnconfigure(1, weight=1)

        ttk.Label(servo_group, text="Angle:").grid(row=0, column=0, sticky=tk.W)

        self.angle_var = tk.IntVar(value=90)
        self.servo_slider = ttk.Scale(servo_group, from_=0, to=180, orient=tk.HORIZONTAL,
                                      variable=self.angle_var, command=self.on_slider_change)
        self.servo_slider.grid(row=0, column=1, sticky="ew", padx=10)

        self.angle_label = ttk.Label(servo_group, text="90°", width=5)
        self.angle_label.grid(row=0, column=2)

    def toggle_connection(self):
        if self.is_connected:
            self.disconnect_from_esp()
        else:
            self.connect_to_esp()

    def connect_to_esp(self):
        ip = self.ip_var.get().strip()
        port_str = self.port_var.get().strip()

        if not ip:
            messagebox.showerror("Error", "IP address cannot be empty.")
            return
        try:
            port = int(port_str)
            if not (0 < port < 65536):
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid port number (1-65535).")
            return
            
        self.save_last_connection_info(ip, port)
        self.connect_button.config(text="Connecting...", state=tk.DISABLED)
        
        # Start the network thread
        self.client_thread = ESP32ClientThread(ip, port, self.gui_queue)
        self.client_thread.start()

    def disconnect_from_esp(self):
        if self.client_thread and self.client_thread.is_alive():
            self.client_thread.close()
        # The thread will put a 'disconnected' message in the queue, which will update the UI.

    def on_slider_change(self, value):
        angle = int(float(value))
        self.angle_label.config(text=f"{angle}°")
        
        # Only send if the angle has changed and we are connected
        if angle != self.last_sent_angle and self.is_connected:
            self.last_sent_angle = angle
            if self.client_thread:
                self.client_thread.send_servo_angle(angle)
    
    def process_queue(self):
        """
        Process messages from the network thread to update the GUI safely.
        """
        try:
            while True:
                message = self.gui_queue.get_nowait()
                if message["status"] == "connected":
                    self.is_connected = True
                    messagebox.showinfo("Success", f"Connected to ESP32 at {self.ip_var.get()}:{self.port_var.get()}")
                elif message["status"] == "disconnected":
                    self.is_connected = False
                elif message["status"] == "error":
                    messagebox.showerror("Connection Error", message["message"])
                    self.is_connected = False # Ensure disconnected state on error
                
                self.update_ui_state()

        except queue.Empty:
            pass # No messages to process
        finally:
            self.after(100, self.process_queue) # Check again in 100ms

    def update_ui_state(self):
        """Enable/disable UI elements based on connection state."""
        if self.is_connected:
            self.connect_button.config(text="Disconnect", state=tk.NORMAL)
            self.servo_slider.config(state=tk.NORMAL)
            self.ip_entry.config(state=tk.DISABLED)
            self.port_entry.config(state=tk.DISABLED)
        else:
            self.connect_button.config(text="Connect", state=tk.NORMAL)
            self.servo_slider.config(state=tk.DISABLED)
            self.ip_entry.config(state=tk.NORMAL)
            self.port_entry.config(state=tk.NORMAL)

    def save_last_connection_info(self, ip, port):
        try:
            with open(CONFIG_FILE, "w") as f:
                f.write(f"{ip}:{port}")
        except IOError as e:
            print(f"Warning: Could not save connection info: {e}")

    def load_last_connection_info(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    ip, port = f.read().strip().split(":")
                    self.ip_var.set(ip)
                    self.port_var.set(port)
            except Exception as e:
                print(f"Warning: Could not load connection info: {e}")
                self.ip_var.set(DEFAULT_IP)
        else:
            self.ip_var.set(DEFAULT_IP)
    
    def on_closing(self):
        self.disconnect_from_esp()
        self.destroy()


if __name__ == "__main__":
    app = ServoControllerApp()
    app.mainloop()
