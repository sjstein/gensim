import simulator
import threading
import time

mini = simulator.GenSimulator()
mini.amp_hours = 10
mini.run_hours = 15


print(f'simulator {mini} info: ip = {mini.gen_ip_num}, tube info = {mini.tube_str} ')

sim_thread = threading.Thread(target=mini.run_simulation, name='GeneratorSim', daemon=True)
print(f'Firing off thread: {sim_thread}')
sim_thread.start()

while True:
    cmd = input('sim:').split(' ')
    if cmd[0] == 'sah':
        mini.amp_hours = int(cmd[1])
    elif cmd[0] == 'sh':
        mini.run_hours = int(cmd[1])
    elif cmd[0] == 'quit':
        exit()
    cmd = None

