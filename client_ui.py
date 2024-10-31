# ui_client.py
import socket
import tkinter as tk
from tkinter import messagebox
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()

    def get_public_key(self):
        return self.public_key

class ClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Client UI")

        self.username_label = tk.Label(root, text="Username:")
        self.username_label.pack(padx=10, pady=5)
        self.username_entry = tk.Entry(root)
        self.username_entry.pack(padx=10, pady=5)

        self.password_label = tk.Label(root, text="Password:")
        self.password_label.pack(padx=10, pady=5)
        self.password_entry = tk.Entry(root, show='*')
        self.password_entry.pack(padx=10, pady=5)

        self.connect_button = tk.Button(root, text="Connect", command=self.connect_to_server)
        self.connect_button.pack(padx=10, pady=10)

        self.message_label = tk.Label(root, text="Message:")
        self.message_label.pack(padx=10, pady=5)
        self.message_entry = tk.Entry(root)
        self.message_entry.pack(padx=10, pady=5)

        self.send_button = tk.Button(root, text="Send Message", command=self.send_message, state=tk.DISABLED)
        self.send_button.pack(padx=10, pady=10)

        self.user = None
        self.server_public_key = None
        self.client = None

    def connect_to_server(self):
        self.user = User(self.username_entry.get(), self.password_entry.get())
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect(('localhost', 5000))

            credentials = f"{self.user.username},{self.user.password}"
            self.client.send(credentials.encode('utf-8'))
            response = self.client.recv(1024).decode('utf-8')
            messagebox.showinfo("Server Response", response)

            if "Authenticated successfully!" in response:
                public_key_data = self.client.recv(1024)
                self.server_public_key = serialization.load_pem_public_key(
                    public_key_data,
                    backend=default_backend()
                )
                self.send_button.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def send_message(self):
        if self.server_public_key:
            message = self.message_entry.get()
            encrypted_message = self.server_public_key.encrypt(
                message.encode('utf-8'),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            self.client.send(encrypted_message)

            # Receive acknowledgment from the server
            ack = self.client.recv(1024)
            decrypted_ack = self.user.private_key.decrypt(
                ack,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            ).decode('utf-8')
            messagebox.showinfo("Server Acknowledgment", decrypted_ack)

if __name__ == "__main__":
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()