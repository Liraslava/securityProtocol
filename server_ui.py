# ui_server.py
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from drone import Drone  # Importing the Drone class


class User:
    def __init__(self, username, password, role):
        self.username = username
        self.password = password
        self.role = role
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()

    def get_public_key(self):
        return self.public_key


class SecurityProtocol:
    def __init__(self):
        self.users = []
        self.current_user = None

    def add_user(self, username, password, role):
        self.users.append(User(username, password, role))

    def authenticate(self, username, password):
        for user in self.users:
            if user.username == username and user.password == password:
                self.current_user = user
                return True
        return False

    def encrypt_data(self, data):
        public_key = self.current_user.get_public_key()
        ciphertext = public_key.encrypt(
            data.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return ciphertext

    def decrypt_data(self, ciphertext):
        plaintext = self.current_user.private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext.decode('utf-8')


class ServerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Server UI")

        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD)
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.sp = SecurityProtocol()
        self.sp.add_user('user1', 'password1', 'operator')

        self.drone = Drone()  # Create an instance of the Drone class

        threading.Thread(target=self.start_server, daemon=True).start()

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('localhost', 5000))
        server.listen(5)
        self.text_area.insert(tk.END, "[STARTING] Server is starting...\n")
        while True:
            conn, addr = server.accept()
            self.text_area.insert(tk.END, f"[NEW CONNECTION] {addr} connected.\n")
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

    def handle_client(self, conn, addr):
        authenticated = False
        while not authenticated:
            credentials = conn.recv(1024).decode('utf-8').split(',')
            if len(credentials) != 2:
                conn.send(b"Invalid credentials format. Use username,password.")
                continue

            username, password = credentials
            authenticated = self.sp.authenticate(username, password)

            if authenticated:
                conn.send(b"Authenticated successfully!")
                self.text_area.insert(tk.END, f"User '{username}' authenticated.\n")
                self.sp.current_user = next(user for user in self.sp.users if user.username == username)
                public_key = self.sp.current_user.get_public_key().public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                conn.send(public_key)
            else:
                conn.send(b"Authentication failed!")

        while True:
            encrypted_message = conn.recv(1024)
            if not encrypted_message:
                break
            try:
                decrypted_message = self.sp.decrypt_data(encrypted_message)
                self.text_area.insert(tk.END, f"[{addr}] Decrypted Message: {decrypted_message}\n")

                # Check for "takeoff" command
                if decrypted_message.lower() == "takeoff":
                    self.drone.take_off()
                    self.text_area.insert(tk.END, "Drone has taken off successfully!\n")

                # Check for "land" command
                if decrypted_message.lower() == "land":
                    self.drone.land()
                    self.text_area.insert(tk.END, "Drone has landed successfully!\n")

                # Send an acknowledgment back, encrypted
                ack_message = "Message received."
                response = self.sp.encrypt_data(ack_message)
                conn.send(response)  # Send acknowledgment back
            except Exception as e:
                self.text_area.insert(tk.END, f"Decryption error: {str(e)}\n")
                conn.send(b"Decryption failed!")

        conn.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = ServerApp(root)
    root.mainloop()