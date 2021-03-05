import simulator
import threading
import socket
import time

myip = '192.168.1.121'
myport = 6001
clientport = 6002


mini = simulator.GenSimulator()


print(f'simulator {mini} info: ip = {mini.gen_ip_num}, tube info = {mini.tube_str}')

sim_thread = threading.Thread(target=mini.run_simulation, name='GeneratorSim', daemon=True)
print(f'Firing off thread: {sim_thread}')
sim_thread.start()


# Set up listener
in_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
out_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
in_sock.bind((myip, myport))
print(f'Opening port {myport} to socket: {in_sock}')

def send_to_client(addr, msg):
    out_sock.sendto(msg.encode('utf-8'), (addr, clientport))

while True:
    data, addr = in_sock.recvfrom(1024)  # BLOCKING READ
    cmd = data.decode('UTF-8').split()
    # print(f'Received {cmd} from {addr}')
    if cmd[0] == 'debug':
        if cmd[1] == 'on':
            mini.debug = True
        else:
            mini.debug = False
    elif cmd[0] == 'flt':
        if len(cmd) < 2:
            # Display all fault words
            resp = (f'Faults = {str.format("0x{:04X}", int(hex(mini.fault_1), 16))} '
                   f'{str.format("0x{:04X}", int(hex(mini.fault_2), 16))} '
                   f'{str.format("0x{:04X}", int(hex(mini.fault_3), 16))} '
                   f'{str.format("0x{:04X}", int(hex(mini.fault_4), 16))} '
                   f'{str.format("0x{:04X}", int(hex(mini.fault_5), 16))} '
                   f'{str.format("0x{:04X}", int(hex(mini.fault_6), 16))} ')
            send_to_client(addr[0], resp)
        elif len(cmd) < 3:
            if cmd[1] == '?':
                resp = 'Usage: flt <opt:num> <opt:val>\n Display or set fault values.'
            else:
                # Display a single fault word
                attr = f'fault_{cmd[1]}'
                word = getattr(mini, attr)
                resp = f'{str.format("0x{:04X}", int(hex(mini.fault_1), 16))}'
            send_to_client(addr[0], resp)
        else:
            # Set a fault word
            setattr(mini, f'fault_{cmd[1]}', int(cmd[2], 0))

    elif cmd[0] == 'null':
        if len(cmd) < 2:
            cmd.append('?')
        if cmd[1] == '?' or len(cmd) != 3:
            resp = (f'null : Command to set a given command response to null for one or more iterations.\n'
                    'usage: null <cmd> <iterations>. If iterations = -1, repeat forever')
            send_to_client(addr[0], resp)
        else:
            mini.nulls[cmd[1]] = int(cmd[2])

    elif cmd[0] == 'set':
        parm = cmd[2]
        try:
            if parm.find('.') == -1:
                val = int(parm)
            else:
                val = float(parm)
        except ValueError:
            val = parm
        try:
            setattr(mini, cmd[1], val)
        except AttributeError:
            resp = 'Usage: set <attribute name> <attribute value>'
            send_to_client(addr[0], resp)
    elif cmd[0] == 'print':
        try:
            resp = f'{cmd[1]} = {getattr(mini, cmd[1])}'
            send_to_client(addr[0], resp)
        except AttributeError:
            resp = 'Usage: set <attribute name> <attribute value>'
            send_to_client(addr[0], resp)
    elif cmd[0] == 'quit':
        exit()
    elif cmd[0] == 'exec':
        try:
            #rval = eval(f'mini.{cmd[1]}()')
            func = getattr(mini, cmd[1])
            rval = func()
            resp = f'{cmd[1]} : {rval}'
            send_to_client(addr[0], resp)
        except AttributeError:
            resp = 'Usage: exec <method name>'
            send_to_client(addr[0], resp)
    cmd = None
