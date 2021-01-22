import simulator

mini = simulator.GenSimulator()

print(f'simulator {mini} info: ip = {mini.gen_ip_num}, tube info = {mini.tube_str} ')
#cmd = input('Enter a command:')

#print(f'Entered the command {cmd}')

#print(mini.execFunc(cmd))
mini.run_simulation()

