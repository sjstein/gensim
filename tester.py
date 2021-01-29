import simulator
import threading
import time

mini = simulator.GenSimulator()


print(f'simulator {mini} info: ip = {mini.gen_ip_num}, tube info = {mini.tube_str}')

sim_thread = threading.Thread(target=mini.run_simulation, name='GeneratorSim', daemon=True)
print(f'Firing off thread: {sim_thread}')
sim_thread.start()

while True:
    cmd = input('sim: ').split(' ')
    if cmd[0] == 'sah':
        mini.amp_hours = int(cmd[1])
    elif cmd[0] == 'sh':
        mini.run_hours = int(cmd[1])
    elif cmd[0] == 'debug':
        if cmd[1] == 'on':
            mini.debug = True
        else:
            mini.debug = False
    elif cmd[0] == 'flt':
        if len(cmd) < 2:
            # Display all fault words
            print(f'Faults = {str.format("0x{:04X}", int(hex(mini.fault_1), 16))} '
                  f'{str.format("0x{:04X}", int(hex(mini.fault_2), 16))} '
                  f'{str.format("0x{:04X}", int(hex(mini.fault_3), 16))} '
                  f'{str.format("0x{:04X}", int(hex(mini.fault_4), 16))} '
                  f'{str.format("0x{:04X}", int(hex(mini.fault_5), 16))} '
                  f'{str.format("0x{:04X}", int(hex(mini.fault_6), 16))} ')
        elif len(cmd) < 3:
            if cmd[1] == '?':
                print('Usage: flt <opt:num> <opt:val>\n Display or set fault values.')
            else:
                # Display a single fault word
                attr = f'fault_{cmd[1]}'
                word = getattr(mini, attr)
                print(f'{str.format("0x{:04X}", int(hex(mini.fault_1), 16))}')
        else:
            # Set a fault word
            setattr(mini, f'fault_{cmd[1]}', int(cmd[2], 0))

    elif cmd[0] == 'set':
        parm = cmd[2]
        if parm.find('.') == -1:
            val = int(parm)
        else:
            val = float(parm)
        try:
            setattr(mini, cmd[1], val)
        except AttributeError:
            print('Usage: set <attribute name> <attribute value>')
    elif cmd[0] == 'print':
        try:
            print(f'{cmd[1]} = {getattr(mini, cmd[1])}')
        except AttributeError:
            print('Usage: print <attribute name>')
    elif cmd[0] == 'quit':
        exit()
    cmd = None

