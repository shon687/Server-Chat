import select
import socket
from pyngrok import ngrok 
client_info = {'Itay':'Itay123' ,'Ron':'Ron123', "Shon": "Shon123"}
server_prompt = "welcome to the chat server! Type c.exit to exit at any moment\nEnter your massage here"
def server_chat():
    # Creating the server socket with IPV4 and TCP by defualt
    server_socket = socket.socket()
    # Allow us to reuse the same address/port if we restart our server quickly
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    incoming_conn = '0.0.0.0'
    PORT = 12345
    # Binding the incoming_conn ip and the port we'll be listening on to the server socket
    server_socket.bind((incoming_conn, PORT))
    # Listen for incoming connections (max of two connection)
    server_socket.listen()
    print(f"Server is listening on {incoming_conn}:{PORT}")
    # Connect port 12345 to ngrok to get a public URL
    public_url = ngrok.connect(addr=PORT, proto='tcp')
    print("Ngrok tunnel opened:", public_url.public_url)
    # Creating a socket list for all the connections including the server socket itself
    sockets_list = [server_socket]
    # Creating a socket to user dict  
    socket_to_user = {}
    # Creating a socket_condition list to store the socket when its successfully verifyed 
    socket_condintion = []
    # Creating an empty dict for every socket
    empty_reads = {}
    # Creating a socket to IP to know every sockets IP
    socket_to_ip = {}
    # Creating a logged_in list for already logged in clients
    logged_in = []
    # Creating a wrong log in variable with the value of zero so that if the client send wrong
    # passwd or username then add 1 untill its 3 and then close connection with the socket.
    wrong_log_in = 0
    # Main loop
    while True:
        # cheking every connection in socket_list if its ready to read from or if there's an error
        readble, _, exceptional = select.select(sockets_list, [], sockets_list)
        for s in readble:
            # if the current socket is the server socket then there's a new connection
            if s is server_socket:
                # Accepting incoming connection and assiging it to a connection var and a client_address var
                (connection, client_address) = server_socket.accept()
                print(f"New connection accepted from {client_address}")
                # Add the new connection to the sockets list
                sockets_list.append(connection)
                # It's not the server socket, so it's a client (connection) sending data
            else:
                # If the client is not already verifyed then receive a username and a passwd
                if s not in socket_condintion:
                    # Getting the client public IP
                    # Verifying that the user is permited to enter the chat server
                    data = s.recv(1024).decode()
                    # If there's no response close the connection
                    if not data:
                         s.close()
                         continue
                    # The client sends a three line ordered information:
                    # 1 - public IP address
                    # 2 - username
                    # 3 - password
                    lines = data.splitlines()
                    public_ip = lines[0]
                    username = lines[1]
                    password = lines[2]
                    # If the username and password is in the client_info dict then notify every other client
                    if username in client_info and password == client_info[username] and username not in logged_in: 
                            print(f"Client {username}:{public_ip} has joined the chat server!")
                            try:
                                for client_socket in sockets_list:
                                    if client_socket != server_socket and client_socket != s:
                                        client_socket.send(f"{username} has joined the chat!".encode())
                            # Add the client socket to all the necessary dictionaries and lists
                            finally:
                                socket_to_user[s] = username
                                socket_to_ip[s] = public_ip
                                socket_condintion.append(s)
                                # Sending a prompt to the client
                                s.send(server_prompt.encode())
                                empty_reads[s] = 0
                                wrong_log_in = 0
                                logged_in.append(username)
                                continue
                    # If the client sent wrong log in info add 1 to wrong_log_in var and send a message "Invalid info"
                    else:
                        wrong_log_in += 1
                        if wrong_log_in < 3:
                            s.send("Invalid information.. ".encode())
                            continue
                        # The client made too many wrong log in attempts so the server closes the socket and removes it from sockets_list
                        else:
                            print(f"Too many wrong login attempts from {public_ip}\nclosing socket.. ")
                            s.send("Too many wrong login attempts.. ".encode())
                            sockets_list.remove(s)
                            s.close()
                # The client is already varifyed and is ready to send massages
                else:
                    try:
                        socket_ip = socket_to_ip[s]
                        print(f"[Chat] reading from {socket_ip}")
                        # Storing the data from the client in a massage var
                        massage = s.recv(1024).decode()
                    except ConnectionResetError:
                        # This happens if the client suddenly disconnected
                        massage = None
                    # If we didn't get any data the client might have client disconnected
                    if not massage:
                        # Setting empty_reads of the current socket + 1 
                        empty_reads[s] += 1
                        # This happens if the client didn't send anything 3 times or more
                        # Closing the client socket and removing it from sockets_list and socket_condition
                        if empty_reads[s] >= 3:     
                            socket_ip = socket_to_ip[s]                   
                            sender_username = socket_to_user[s] 
                            print(f"client {sender_username}:{socket_ip} disconnected.. ")
                            sockets_list.remove(s)
                            s.close()
                            socket_condintion.remove(s)
                            continue
                        # If the client sent nothing under 3 times notify the server and continue trying to read from the client
                        else:
                             sender_username = socket_to_user[s]
                             print(f"Client {sender_username} sent nothing.. ")
                             continue
                    # we got a massage and we're ready to broadcast it to other clients
                    else:
                        # we reset empty_reads to zero
                        empty_reads[s] = 0
                        
                        # The client wants to disconnect
                        if massage == "c.exit":
                            s.send("Connection terminated.. ".encode())
                            sender_username = socket_to_user[s]
                            print(f"Client {sender_username} disconnected.. ")
                            # Notify the other clients about the user's disconnection
                            # Removing the client socket from sockets_list and socket_condition
                            for client_socket in sockets_list:
                                if client_socket != server_socket and client_socket != s:
                                    client_socket.send(f"{sender_username} left the chat.".encode()) 
                            sockets_list.remove(s)
                            s.close()
                            socket_condintion.remove(s)
                            logged_in.remove(sender_username)
                        # The client wants to send a massage to other clients
                        else:
                                socket_ip = socket_to_ip[s]
                                print(f"Received massage {massage} from {socket_ip}")
                                # Ittirate over every socket in sockets_list to send them the massage except for the server_socket and the sender
                                sender_username = socket_to_user[s] 
                                for client_socket in sockets_list:
                                    if client_socket != server_socket and client_socket != s:
                                        client_socket.send(f"{sender_username}:{massage}".encode())
            
            # If the socket has an error we remove and close the socket
            for bad_socket in exceptional:
                sockets_list.remove(bad_socket)
                bad_socket.close()
                socket_condintion.remove(bad_socket)
main = server_chat()
print(main)
