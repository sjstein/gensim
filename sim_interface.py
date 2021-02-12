import tkinter as tk
import socket
import time

sup_ip = '192.168.1.121'
my_ip = '192.168.1.99'
#my_ip = '192.168.1.60'
sup_port = 6001
in_port = 6002

out_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
in_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
in_socket.settimeout(1)     # How long to wait for a message before exception
in_socket.bind((my_ip, in_port))
print(f'Bound to input socket: {in_socket}')


def exec_null():
    cmd = f'null {func_var.get()} {ent_null_tgt.get()}'
    out_socket.sendto(cmd.encode('utf-8'), (sup_ip, sup_port))
    return

def exec_door_flt():
    cmd = f'set fault_1 2'
    out_socket.sendto(cmd.encode('utf-8'), (sup_ip, sup_port))
    return

def exec_pres_flt():
    cmd = f'set fault_1 1'
    out_socket.sendto(cmd.encode('utf-8'), (sup_ip, sup_port))
    return

def exec_eeprom_flt():
    cmd = f'set fault_1 8'
    out_socket.sendto(cmd.encode('utf-8'), (sup_ip, sup_port))
    return

def exec_hv_hi_flt():
    cmd = f'set fault_2 64'
    out_socket.sendto(cmd.encode('utf-8'), (sup_ip, sup_port))
    return

def exec_hv_lo_flt():
    cmd = f'set fault_2 128'
    out_socket.sendto(cmd.encode('utf-8'), (sup_ip, sup_port))
    return

def make_label(root, wid, r, c):
    lbl = tk.Label(master=root, text='0', relief=tk.RIDGE, width=wid, padx=5, pady=5)
    lbl.grid(row=r, column=c, padx=2)
    return lbl


window = tk.Tk()
window.title("Operator display : Generator Simulation Engine")
# Organize GUI into frames:
# Frame 1: Generator status
# Frame 2: Faults
# Frame 3: Network injection
# Frame 4: Simulation control
# Frame 5: Fault control
fr1 = tk.LabelFrame(window, text='Generator status', pady=3, bg='#dddddd')
fr2 = tk.LabelFrame(window, text='Generator faults', pady=3)
fr3 = tk.LabelFrame(window, text='Network inject', pady=3)
fr4 = tk.LabelFrame(window, text='Simulation control', pady=3)
fr5 = tk.LabelFrame(window, text='Fault control', pady=3)


# Labels
lbl_accel_current = make_label(fr1, 20, 0, 0)
lbl_accel_voltage = make_label(fr1, 20, 0, 1)
lbl_getter_current = make_label(fr1, 20, 0, 2)
lbl_system_state = make_label(fr1, 20, 0, 3)
lbl_intlk_state = make_label(fr1, 20, 0, 4)
lbl_neut_state = make_label(fr1, 20, 0, 5)

lbl_fault_1 = make_label(fr2, 20, 1, 0)
lbl_fault_2 = make_label(fr2, 20, 1, 1)
lbl_fault_3 = make_label(fr2, 20, 1, 2)
lbl_fault_4 = make_label(fr2, 20, 1, 3)
lbl_fault_5 = make_label(fr2, 20, 1, 4)
lbl_fault_6 = make_label(fr2, 20, 1, 5)

lbl_fault_list = [lbl_fault_1,
                  lbl_fault_2,
                  lbl_fault_3,
                  lbl_fault_4,
                  lbl_fault_5,
                  lbl_fault_6]

# Entry fields
ent_null_tgt = tk.Entry(master=fr3, width=5)
ent_null_tgt.insert(0, '1')
ent_null_tgt.grid(row=0, column=1, padx=0)

ent_attr_tgt = tk.Entry(master=fr4, width=5)
ent_attr_tgt.insert(0, '0')
ent_attr_tgt.grid(row=0, column=1, padx=0)

# Buttons
btn_null = tk.Button(master=fr3, text="SET NULL", command=exec_null)
btn_null.grid(row=0, column=0, pady=0, padx=0)

btn_fault_door = tk.Button(master=fr5, text=" DOOR ", command=exec_door_flt)
btn_fault_door.grid(row=0, column=0, pady=0, padx=2)

btn_fault_pres = tk.Button(master=fr5, text="PRESS", command=exec_pres_flt)
btn_fault_pres.grid(row=0, column=1, pady=0, padx=2)

btn_fault_eeprom = tk.Button(master=fr5, text="EEPROM", command=exec_eeprom_flt)
btn_fault_eeprom.grid(row=0, column=2, pady=0, padx=2)

btn_fault_hvhi = tk.Button(master=fr5, text="HV-HIGH", command=exec_hv_hi_flt)
btn_fault_hvhi.grid(row=0, column=3, pady=0, padx=2)

btn_fault_hvlo = tk.Button(master=fr5, text="HV-LOW ", command=exec_hv_hi_flt)
btn_fault_hvlo.grid(row=0, column=4, pady=0, padx=2)

func_list = ['MAC',
             'MAH',
             'MAV',
             'MBC',
             'MEI',
             'MFA',
             'MFG',
             'MH',
             'MI',
             'MP',
             'MRC',
             'MRR',
             'MRV',
             'MSV',
             'MTC',
             'MTD',
             'MTP',
             'MTS',
             'MTT']

attr_list = ['IDEAL_TUBE_PRES',
             'IDEAL_TUBE_TEMP',
             'IDEAL_INPUT_EMF',
             'IDEAL_BOARD_TEMP',
             'GETTER_IDLE',
             'GETTER_RAMP',
             'GETTER_RUNNING',
             'ACCEL_VOLTAGE_WARM',
             'NEUTRONS_RAMP_TIME',
             'ACCEL_CURRENT_NOISE',
             'ACCEL_VOLTAGE_NOISE',
             'GETTER_CURRENT_NOISE',
             'ENV_NOISE',
             ]

# Drop downs
func_var = tk.StringVar(window)
func_var.set(func_list[0])
opt_null_func = tk.OptionMenu(fr3, func_var, *func_list)
opt_null_func.config(width=15)
opt_null_func.grid(row=0, column=2)

attr_var = tk.StringVar(window)
attr_var.set(attr_list[0])
opt_attr = tk.OptionMenu(fr4, attr_var, *attr_list)
opt_attr.config(width=30, font=('Futura', 8))
opt_attr['menu'].configure(font=('Futura', 10))
opt_attr.grid(row=0, column=0)

fr1.grid(row=0, column=0)
fr2.grid(row=1, column=0)
fr3.grid(row=2, column=0, sticky='W')
fr4.grid(row=3, column=0, sticky='W')
fr5.grid(row=4, column=0, sticky='W')

def update_labels():
    cmd = 'print accel_current'
    out_socket.sendto(cmd.encode('utf-8'), (sup_ip, sup_port))
    data, addr = in_socket.recvfrom(1024)  # Will wait for socket.timeout before throwing exception
    rval = float(data.split()[2].decode("utf-8"))
    lbl_accel_current['text'] = f'Accel Current: {rval:06.2f}'

    cmd = 'print accel_voltage'
    out_socket.sendto(cmd.encode('utf-8'), (sup_ip, sup_port))
    data, addr = in_socket.recvfrom(1024)  # Will wait for socket.timeout before throwing exception
    rval = float(data.split()[2].decode("utf-8"))
    lbl_accel_voltage['text'] = f'Accel Voltage: {rval:06.2f}'

    cmd = 'print getter_current'
    out_socket.sendto(cmd.encode('utf-8'), (sup_ip, sup_port))
    data, addr = in_socket.recvfrom(1024)  # Will wait for socket.timeout before throwing exception
    rval = float(data.split()[2].decode("utf-8"))
    lbl_getter_current['text'] = f'Getter Current: {rval:04.2f}'

    cmd = 'print system_state'
    out_socket.sendto(cmd.encode('utf-8'), (sup_ip, sup_port))
    data, addr = in_socket.recvfrom(1024)  # Will wait for socket.timeout before throwing exception
    rval = int(data.split()[2].decode("utf-8"))
    lbl_system_state['text'] = f'System State: {rval}'

    cmd = 'print faults'
    out_socket.sendto(cmd.encode('utf-8'), (sup_ip, sup_port))
    data, addr = in_socket.recvfrom(1024)  # Will wait for socket.timeout before throwing exception
    if eval(data.split()[2].decode("utf-8")):
        lbl_intlk_state['bg'] = '#ff1111'
        lbl_intlk_state['text'] = f'Interlocks: TRIP'
    else:
        lbl_intlk_state['bg'] = '#11ee11'
        lbl_intlk_state['text'] = f'Interlocks: OK'

    cmd = 'print neutrons_on'
    out_socket.sendto(cmd.encode('utf-8'), (sup_ip, sup_port))
    data, addr = in_socket.recvfrom(1024)  # Will wait for socket.timeout before throwing exception
    if eval(data.split()[2].decode("utf-8")):
        lbl_neut_state['bg'] = '#8b008b'
        lbl_neut_state['text'] = f'Neutrons: ON'
    else:
        lbl_neut_state['bg'] = '#eeeeee'
        lbl_neut_state['text'] = f'Neutrons: OFF'

    for i in range(1, 7):
        cmd = f'print fault_{i}'
        out_socket.sendto(cmd.encode('utf-8'), (sup_ip, sup_port))
        try:
            data, addr = in_socket.recvfrom(1024)  # Will wait for socket.timeout before throwing exception
        except socket.timeout:
            pass
        rval = int(data.split()[2].decode("utf-8"))
        if rval > 0:
            lbl_fault_list[i-1]['bg'] = '#ff0000'
        else:
            lbl_fault_list[i - 1]['bg'] = '#eeffee'
        lbl_fault_list[i-1]['text'] = f'Fault {i}: {rval:016b}'

    window.after(2000, update_labels)


def callback(*args):
    cmd = f'print {attr_var.get()}'
    print(f'In callback sending : {cmd}')
    out_socket.sendto(cmd.encode('utf-8'), (sup_ip, sup_port))
    data, addr = in_socket.recvfrom(1024)  # Will wait for socket.timeout before throwing exception
    rval = data.split()[2].decode("utf-8")
    print(f'In callback with return of {rval}')
    ent_attr_tgt.delete(0, "end")
    ent_attr_tgt.insert(0, rval)


def set_attribute(*args):
    val = ent_attr_tgt.get()
    cmd = f'set {attr_var.get()} {val}'
    out_socket.sendto(cmd.encode('utf-8'), (sup_ip, sup_port))
    print(f'Sent cmd: {cmd}')


ent_attr_tgt.bind('<Return>', set_attribute)

attr_var.trace("w", callback)
update_labels()
window.mainloop()

while True:
    cmd = input('Enter command: ')
    cmdbytes = cmd.encode('utf-8')
    out_socket.sendto(cmdbytes, (sup_ip, sup_port))
    try:
        data, addr = in_socket.recvfrom(1024)  # Will wait for socket.timeout before throwing exception
        print(f'{addr} sent: {data}')
    except socket.timeout:
        print(f'[{time.strftime("%H:%M:%S", time.localtime())}] UDP receive timeout (no response from server)')


