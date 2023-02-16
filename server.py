import ast
import socket
from threading import Thread

SERVER_HOST = ""
SERVER_PORT = 5002
config_ipv4 = (SERVER_HOST, SERVER_PORT)
separator_token = "<SEP>"
name_token = "<NAME>"
group_creation_token = "<GROUPCREATE>"
no_names_token = "<NONAMES>"
names_token = "<NAMES>"
get_existing_chats = "<GETCHATS>"
no_groups_token = "<NOGROUPS>"
group_message_token = "<GROUPMSG>"


client_sockets = []
clients_dict = {}
group_chats = {"TEST": []} #key - name, value - users list
to_deliver = {} #key - name of the user, value - list of messages
#s = socket.socket()
s = socket.create_server(config_ipv4, family=socket.AF_INET6, dualstack_ipv6=True)
#s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.listen(10)
print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

def name_handler(msg, clientSocket):
    name_split = msg.split(name_token)
    if name_split[1] not in clients_dict:
        clients_dict[name_split[1]] = clientSocket
        for client_socket in client_sockets:
            client_socket.send(f"User {name_split[1]} has entered the chat!\n".encode())
    print("To deliver: ", to_deliver)
    print("Name: ", name_split[1])
    if name_split[1] in to_deliver.keys():
        print("Should sent the messages")
        clientSocket.send(f"You have some unread messages:".encode())
        for message in to_deliver[name_split[1]]:
            clientSocket.send(("UNREAD: "+message).encode())

def direct_message(splitted_msg, sender_socket):
    message = splitted_msg[0]
    reciever = splitted_msg[1]
    if reciever in clients_dict and clients_dict[reciever] in client_sockets:
        clients_dict[reciever].send(message.encode())
    else:
        sender_socket.send(f"User {reciever} isn't connected. Message will be sent when they connect.\n".encode())
        if reciever in to_deliver:
            to_deliver[reciever] += [message]
        else:
            to_deliver[reciever] = [message]

def listen_for_messages(cs):
    while True:
        try:
            msg = cs.recv(1024).decode()
        except Exception as exception:
            print(f"[!] Error: {exception}")
            client_sockets.remove(cs)
        else:
            if msg.contains("<NAME>"):
                name_handler(msg, cs)
            elif msg.contains("<END>"):
                end_split = msg.split("<END>")
                for client_socket in client_sockets:
                    client_socket.send(end_split[1].encode())
                client_sockets.remove(cs)
            elif msg.contains(group_creation_token):
                group_split = msg.split(group_creation_token)
                group_name = group_split[0]
                group_members = group_split[1].split(", ")
                group_chats[group_name] = group_members
            elif msg.contains(get_existing_chats):
                chats_string = str(group_chats)
                if chats_string != "":
                    chats_string_tokened = get_existing_chats + chats_string + get_existing_chats
                    cs.send(chats_string_tokened.encode())
                else:
                    client_socket.send(no_groups_token.encode())
            elif msg.contains(group_message_token):
                msg_split = msg.split(group_message_token)
                message = msg_split[0]
                members = msg_split[1]
                members = ast.literal_eval(msg_split[1])
                for member in members:
                    clients_dict[member].send(message.encode())
            else:
                splitted_msg = msg.split(separator_token)
                if len(splitted_msg) == 2:
                    direct_message(splitted_msg, cs)
                else:
                    for client_socket in client_sockets:
                        client_socket.send(msg.encode())


while True:
    client_socket, client_address = s.accept()
    print(f"[+] {client_address} connected.")
    client_sockets.append(client_socket)

    names_list = list(clients_dict.keys())
    names_string = '{separator_token}'.join(names_list)
    if names_string != "":
            names_string_tokened = names_token + names_string + names_token
            client_socket.send(names_string_tokened.encode())
    else:
        client_socket.send(no_names_token.encode())
    
    t = Thread(target=listen_for_messages, args=(client_socket,))
    t.daemon = True
    t.start()

# Unused for now
for cs in client_sockets:
    cs.close()
s.close()