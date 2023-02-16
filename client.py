import ast
import socket
import random
from threading import Thread
from datetime import datetime
from colorama import Fore, init
import time
import copy




# init colors
init()

colors = [Fore.BLUE, Fore.CYAN, Fore.GREEN, Fore.LIGHTBLACK_EX, 
    Fore.LIGHTBLUE_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTGREEN_EX, 
    Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.LIGHTWHITE_EX, 
    Fore.LIGHTYELLOW_EX, Fore.MAGENTA, Fore.RED, Fore.WHITE, Fore.YELLOW
] 

client_color = random.choice(colors)

SERVER_INFO = socket.getaddrinfo('localhost', 5002)
SERVER_IPV4 = SERVER_INFO[1][4]
SERVER_IPV6 = SERVER_INFO[0][4]
separator_token = "<SEP>"
name_token = "<NAME>"
names_token = "<NAMES>"
admin_token = "<ADMIN>"
group_creation_token = "<GROUPCREATE>"
get_existing_chats = "<GETCHATS>"
group_message_token = "<GROUPMSG>"
no_names_token = "<NONAMES>"
s = socket

names = []
existing_chats = {}

def listen_for_messages():
    while True:
        global existing_chats
        global names
        message = s.recv(1024).decode()
        if get_existing_chats in message:
            #handle chat adding
            splitted_chats = message.split(get_existing_chats)
            existing_chats = ast.literal_eval(splitted_chats[1])
        elif names_token in message:
            message = message.replace(names_token, "")
            names = message.split(separator_token)
        elif no_names_token in message:
            names= []
            message = message.replace(no_names_token, "")
            print(message)
        else:
            print(message)

def direct_message():
    reciever = input("Entered the direct message mode. Type a name of the reciever:")
    print("Type the message. Type 'qd' to return to the general chat:")
    to_send = input()
    while True:
        if(to_send == "qd"):
            print("Returning to general chat...")
            return
        to_send = f"{client_color}[{date_now}] {name}: {to_send}{Fore.RESET}{separator_token}{reciever}"
        s.send(to_send.encode())
        to_send = input()

def create_group_chat():
    s.send((get_existing_chats).encode())
    time.sleep(0.3)
    print("Entered the group chat creation mode. Type a name of the group:")
    group_name = input()
    while group_name in existing_chats and ("<") in group_name or (">") in group_name:
        if ("<") in group_name or (">") in group_name:
            group_name =  input("Group name cannot have the following characters: < or >. Please type a new name: \n")
        else:
            group_name = input("That name is taken! Type a different name of the group:")

    print("Who will be in the group? Type a names with comas between them to add users to the group?")
    members = input()
    if len(members) != 0:
        members += ", " + (admin_token+name+admin_token)
        s.send((group_name+group_creation_token+members).encode())
        print("Group created! Returning to the general chat...")
    else:
        print("You can't create an empty group! Returning to the general chat...")

def send_to_group_chat():
    anwser = "Y"
    s.send((get_existing_chats).encode())
    time.sleep(0.3)
    part_of = {}
    for (key, value) in existing_chats.items():
        if name in value or admin_token+name+admin_token in value:
            part_of[key] = value
    if not part_of:
        print("You are not a part of any group")
        return
    print(f"Groups that you are a part of: ")
    working_copy = copy.deepcopy(part_of)
    for key, value in working_copy.items():
        for member in value:
            if admin_token in member:
                    value.remove(member)
                    value.append(member.split(admin_token)[1])
                    break
        print(f"Name {key}. Members: {', '.join(value)}\n")
    whatGroup = input("To what group do you want to write?\n")
    while whatGroup not in part_of.keys():
        print("That group doesn't exists or you don't have access to it! Choose a different group or quit (qc): ", part_of)
        whatGroup = input()
        if whatGroup == 'qc':
            print("Returning to the general chat...")
            return
    
    chosen_group_members = part_of[whatGroup]
    chosen_group_name = whatGroup
    
    if admin_token+name+admin_token in chosen_group_members:
        print("You have admin priviliges in this group. Do you wish to perform administrative actions? [Y/N]")
        anwser = input()
        if anwser == "Y":
            print("To add member, type add [name], to delete members type delte [member]. To delete the group type delete [this group's name]. To exit type qa")
            action = input()
            while True:
                if action == 'qa':
                    print("Exiting admin mode...")
                    break
                elif "delete" in action:
                    to_remove = action.split()[1]
                    if to_remove in chosen_group_members:
                        chosen_group_members.remove(to_remove)
                        print(f"User {to_remove} has been removed!")

                    else:
                        print(f"No user {to_remove} found in the group!")
                elif "add" in action:
                    to_add = action.split()[1]
                    print("Current members: ", chosen_group_members)
                    if to_add not in chosen_group_members:
                        chosen_group_members.append(to_add)
                        break
                    else:
                        print("This user is alredy in the group!")
                elif action == f"delete {chosen_group_name}":
                    print("Deleting...")
                    existing_chats.pop(chosen_group_name)
                action = input()

    print("Type the message. Type 'qc' to return to the general chat:")
    to_send = input()
    while True:
        if ("<") in to_send or (">") in to_send:
            print("Message cannot have the following characters: < or >. Please type a new message: \n")
        elif(to_send == "qc"):
            print("Returning to general chat...")
            if anwser == "Y":
                s.send((chosen_group_name+group_creation_token+''.join(chosen_group_members)).encode())
            return
        else:
            for member in chosen_group_members:
                if admin_token in member:
                    chosen_group_members.remove(member)
                    chosen_group_members.append(member.split(admin_token)[1])
            formatted = f"{client_color}[{date_now}] {name} from group {chosen_group_name}: {to_send}{Fore.RESET}{group_message_token}{chosen_group_members}"
            s.send(formatted.encode())
        to_send = input()



client_ip = input("Welcome. Would you like to connect using IPv4 or IPv6? [4/6]")
if client_ip == "6":
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0) #ERROR here
else:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    if client_ip == "6":
        print("IPV6:", SERVER_IPV6)
        s.connect(SERVER_IPV6)
    else:
        s.connect(SERVER_IPV4)
    print("[+] Connected.")
except Exception as exception:
    print(f"[!] Error : {exception}")


        

t = Thread(target=listen_for_messages)
t.daemon = True
t.start()
name = input("Enter your username: ")
while ("<") in name or (">") in name or name in names:
    if name in names:
        name = input("That name is taken!. Please type a new name.\n")
    else:
        name = input("Name cannot have the following characters: < or >. Please type a new name.\n")
name_toSend = name_token + name + name_token
s.send(name_toSend.encode())

print("Welcome! Just type to send messages. Type q to quit. To enter direct message mode type direct. To send to group chat type 'group'. To create a new groupchat type 'cg'\n")


while True:
    date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S') #unneccessary but cool
    to_send =  input()
    if  ("<") in to_send or (">") in to_send:
        print("Message cannot have the following characters: < or >. Please type a new message: \n")
    elif to_send.lower() == 'q':
        break
    elif to_send.lower() == 'direct':
        direct_message()
    elif to_send.lower() == 'group':
        send_to_group_chat()
    elif to_send.lower() == 'cg':
        create_group_chat()
    elif to_send.lower() != 'direct' and to_send.lower() != 'CG' and to_send.lower != 'group': 
        to_send = f"{client_color}[{date_now}] {name}: {to_send}{Fore.RESET}"
        s.send(to_send.encode())
print("Ending the connection...")
s.send(f"<END>User {name} has left the chat.<END>".encode())
s.close()