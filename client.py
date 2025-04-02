import socket
import threading
import requests

def receive_messages(client_socket):
    # Continuously listen for data from the server and print it.
    while True:
        try:
            data = client_socket.recv(1024).decode()
            # If the server didn't send anything then the server closed the connection
            # Notify the client
            if not data:
                print("Server closed the connection.")
                break
            # If the server sent something print it to the user
            print(data)
        except:
            # If an error occurred while receiving data from the server notify the client and break
            print("Error receiving data from server.")
            break

def client1():
    # Asking the user for the ngrok public URL to access the local server
    public_url = input("Enter ngrok public URL here\n> ")
    # In order to bind the URL and port to the client socket I need to get rid of irrelevant information in the URL
    # Replacing "tcp://" with an empty string
    replace = public_url.replace("tcp://", "")
    # Spliting the URL from the ":", the first part is for the host and the second is the port as a string
    host, port_str = replace.split(":")
    # Setting port as an integer
    port = int(port_str)

    # Creat a client socket with TCP and IPV4 by defualt
    client_socket = socket.socket()
    # Connect to the server
    client_socket.connect((host, port))
    print("Connected to server via Ngrok tunnel!")
    # Get public IP
    try:
        # Make an HTTP GET request to ipify service
        response = requests.get("http://api64.ipify.org?format=json")
        # Using json to gt the IP (ipify service returns a json format)
        public_ip = response.json().get("ip", "Unknown")
    except:
        # If it fails then public IP is set to "Unknown"
        public_ip = "Unknown"
    # Creating a wrong_log_in var that is set to 0
    wrong_log_in = 0
    while True:
        # Ask for a username and a password
        username = input("Enter your username\n> ")
        password = input("Enter your password\n> ")

        # Send login info in 3 separated lines
        client_socket.send(f"{public_ip}\n{username}\n{password}".encode())

        # Receive initial response
        welcome = client_socket.recv(1024).decode()
        # If the server response with "Invalid info" then add 1 to wrong_log_in and 
        # continue asking for the right username and password if wrong_log_in is under 3
        if welcome == "Invalid information.. ":
            wrong_log_in += 1
            print(welcome)
            if wrong_log_in <= 3:
                continue
            else:
                # If wrong_log_in is equel or grater then 3 then exit
                too_many_attempts = client_socket.recv(1024).decode()
                print(too_many_attempts)
                client_socket.close()
                # By returning I quit the function
                return
        else:
            # The info is valid so I'm printing the welcome message from the server
            print(welcome)
            break
        # Continue to the messaging phase
    # Start a separate thread to continuously receive and print messages from server
    receiver_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    # we set receiver_thread to deamon = True, so that the main program won't wait for the thread to finish and will just exit
    receiver_thread.daemon = True
    receiver_thread.start()

    # Main loop for sending messages
    while True:
        # Asking for the user an input and storing it in a "message" var 
        message = input("> ")
        # If the user wants to disconnect from the server then send this "commend" to the server,
        # Receive a confirmation for the disconnection, break from the loop and close the client_socket
        if message == "c.exit":
            client_socket.send(message.encode())
            server_response = client_socket.recv(1024).decode()
            print(server_response)
            break
        # The user wants to send a message to other clients
        # so I'm sending it to the server in order for that to get broadcasted to everyone else
        else:
            client_socket.send(message.encode())

    client_socket.close()

client1()
