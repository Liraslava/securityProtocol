# SecurityProtocol

We have added methods to our code to generate public/private key pairs for each user, data is encrypted before transmission, and data is decrypted after reception. 

We have implemented asymmetric encryption using RSA.
(In the future, you can think about creating your own algorithm)

The structure of our protocol

1. Authentication — it is necessary for the drone to be sure of the authenticity of the operator:

    - the contents of the IP packet — the original data has not been changed, their integrity has not been violated, they are not available for retransmission.
    - the sender of the data — the source data was created by exactly who it is claimed.

Authentication will be performed using a pre-key exchange.

2. Pre-Shared Key Exchange (PSK)
Pre—key exchange is an authentication method that is based on the pre-distribution of keys between data exchange participants. After establishing a shared key, they can use it for both encryption and decryption of data.

Assumptions:
Vulnerability — can be compromised if the key becomes known to third parties.
Risk of leakage — in case of compromise of the key, all data for which this key was used will be at risk of decryption.


How the code works:

We have created a simple client-server architecture using the socket library built into Python. 
The server processes user authentication and encrypts/decrypts messages, while the client sends messages to the server.

1. The server (server.py ):
- The server listens for incoming connections on localhost and port 5000.
   - When the client connects, it creates a new thread to process the client.
   - The server authenticates the user based on the username and password sent by the client.
   - After successful authentication, the server sends its public key to the client.
   - The server listens to encrypted messages from the client, decrypts them and prints the decrypted message.
   - He sends the confirmation back to the client.

2. The client (client.py ):
- The client connects to the server and sends his username and password for authentication.
   - After successful authentication, he receives the public key of the server.
   - The client encrypts the message using the server's public key and sends it to the server.
   - Then it waits for confirmation from the server, decrypts it and prints it.


What needs to be improved:

Our prototype demonstrates a basic implementation of secure client-server communication using asymmetric encryption for message transmission.
- In a production application, we need to consider adding error handling, logging, and more robust security measures such as secure key exchange and user management.
- Check that exceptions and extreme cases (e.g. incorrect input, connection problems) are handled properly.
