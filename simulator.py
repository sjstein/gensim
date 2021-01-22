class GenSimulator:
    """
    Generator simulator class

    Attributes of base class:
        gen_type:
            one of : ['P385','P383','MINI']
        tube_str:
            string  (ex: '123DT')
        gen_ip_num:
            string representing IPv4 address
        gen_inp_port:
            int (port for incoming UDP commands)
        gen_out_port:
            int (port for outgoing UDP commands)
    """
    # default address and port assignments
    gen_ip_num = '192.168.1.121'
    gen_inp_port = 55556
    gen_out_port = 55555
    beam_value = 0
    pulse_freq = 5000
    pulse_width = 0
    pulse1_delay = 0
    pulse1_width = 45
    pulse2_delay = 0
    pulse2_width = 0
    pulse3_delay = 0
    pulse3_width = 0
    duty_factor = 0
    current_state = 32


    def __init__(self, gen_type='MINI', tube_str='235DT'):
        self.gen_type = gen_type
        self.tube_str = tube_str

    def exec_func(self, inst_lst):
        func = getattr(self, inst_lst.pop(0))
        print(f'In exec_func, called with: {inst_lst} and func = {func}')
        return func(inst_lst)

    def run_simulation(self):
        import re
        import socket
        import time

        in_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        out_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        in_sock.bind((self.gen_ip_num, self.gen_inp_port))

        faults = True  # Set this to True to indicate generator fault(s)
        # Modify this to simulate different types of faults represented by status bits

        def strip_msg(bdata):
            sdata = bdata.decode('UTF-8')
            pat = re.compile('\$[a-z](.+?)#')  # Match all characters between $? and #
            m = pat.match(sdata)
            return m.group(0)[1], m.group(1).split(' ')

        def send_msg(message, addr, seq):
            chk = generate_checksum(seq + ' ' + message)
            respstr = f'{seq} {message}#{chk[2:].zfill(2)}\r'
            # respstr = f'{seq}{message}#{chk}\r\x00'
            respbytes = respstr.encode('utf-8')  # Convert string to byte object
            print(f'Sending {respbytes} to {addr}')
            out_sock.sendto(respbytes, (addr, self.gen_out_port))

        def generate_checksum(message):
            s = 0
            for i in range(len(message)):
                s += ord(message[i])
            return hex(~s & 0xff).upper()   # Mask to one byte, invert and return
                                            # Using uppercase to deal with strange client requirement

        while True:
            data, addr = in_sock.recvfrom(1024)  # BLOCKING READ
            seq, msg = strip_msg(data)
            # print(f'{addr[0]} sent msg: {data} extracted to: {msg} with seq: {seq}')
            print(f'Received : {seq} : {msg} ({type(msg)})')
            # print(f'msg checksum = {generate_checksum(seq+msg)}')
            time.sleep(0.05)  # Delay response from command just a bit
            while len(msg) > 0:
                print(f'calling exec_func({msg})')
                resp = self.exec_func(msg)
                send_msg(resp, addr[0], seq)


    def U(self, cmd_lst):
        """
        This is a weird undocumented command
        """
        if cmd_lst.pop(0) == 'TMFP':
            return '1'

    def SUT(self, cmd_lst):
        """
        Sets the auto shut down time (if enabled) in seconds.
        :param cmd_lst[0]:
        :return: '0'
        """
        parm = cmd_lst.pop(0)
        # Do something with parm to affect simulation
        return '0'

    def MBC(self):
        """
        Monitor Beam Current

        Returns float
        """
        return '0.000'

    def MAV(self):
        """
        Monitor Accelerator Voltage

        returns:
            float
        """
        return '0.000'

    def MRC(self):
        """
        Monitor Reservoir Current

        returns:
            float
        """
        return '0.000'

    def MFA(self):
        """
        Monitor Fault Analysis
        """
        return '0x0000 0x0000 0x0000 0x0000 0x0000 0x0000'

    def MF1(self):
        """
        Monitor Fault Analysis
        """
        return '0'

    def MF2(self):
        """
        Monitor Fault Analysis
        """
        return '0'

    def MF3(self):
        """
        Monitor Fault Analysis
        """
        return '0'

    def MF4(self):
        """
        Monitor Fault Analysis
        """
        return '0'

    def MF5(self):
        """
        Monitor Fault Analysis
        """
        return '0'

    def MF6(self):
        """
        Monitor Fault Analysis
        """
        return '0'

    def RCAT(self):
        """

        :return:
        """
        return f'TUBE{self.tube_str}'

    def SBV(self, cmd_lst):
        self.beam_value = int(cmd_lst.pop(0))
        # Do something with parm to affect simulation
        return '0'

    def RPF(self):
        return f'{self.pulse_freq}'

    def RPD(self):
        return f'{self.duty_factor}'

    def RP1D(self):
        return f'{self.pulse1_delay}'

    def RP1W(self):
        return f'{self.pulse1_width}'

    def MP(self):
        return f'{self.current_state}'
