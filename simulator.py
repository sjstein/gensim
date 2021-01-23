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

    amp_hours = 0
    beam_value = 0
    board_temp = 32.5
    current_state = 32
    duty_factor = 0
    faults = True
    pulse_freq = 5000
    pulse_width = 0
    pulse1_delay = 0
    pulse1_width = 45
    pulse2_delay = 0
    pulse2_width = 0
    pulse3_delay = 0
    pulse3_width = 0
    run_hours = 0
    tube_pres = 120.003
    tube_temp = 21.99

    msg_list = []

    def __init__(self, gen_type='MINI', tube_str='235DT'):
        self.gen_type = gen_type
        self.tube_str = tube_str

    def exec_func(self):
        cmd = self.msg_list.pop(0)
        try:
            func = getattr(self, cmd)
        except AttributeError:
            print(f'Generator simulation: unknown message received: {cmd}')
            func = getattr(self, 'null_cmd')
        return func()

    def run_simulation(self):
        import re
        import socket
        import time

        resp_list = []

        in_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        out_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        in_sock.bind((self.gen_ip_num, self.gen_inp_port))

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
            # print(f'Sending {respbytes} to {addr}')
            out_sock.sendto(respbytes, (addr, self.gen_out_port))

        def generate_checksum(message):
            s = 0
            for i in range(len(message)):
                s += ord(message[i])
            return hex(~s & 0xff).upper()   # Mask to one byte, invert and return
                                            # Using uppercase to deal with strange client requirement

        while True:
            data, addr = in_sock.recvfrom(1024)  # BLOCKING READ
            seq, self.msg_list = strip_msg(data)
            # print(f'Received : {seq} : {self.msg_list}')
            time.sleep(0.05)  # Delay response from command just a bit
            resp_list.clear()
            while len(self.msg_list) > 0:
                resp_list.append(self.exec_func())
            if len(resp_list) > 1:
                resp = ' '.join(resp_list)
            else:
                resp = resp_list[0]
            send_msg(resp, addr[0], seq)

    def null_cmd(self):
        """
        Entrypoint for all unknown commands
        :return:
        """
        return '0'

    def C(self):
        """
        Clear faults
        :return:
        """
        self.faults = False
        self.current_state = 256
        return '0'

    def MAH(self):
        """
        Monitor Amp Hours

        Returns float
        """
        return f'{self.amp_hours}'

    def MAV(self):
        """
        Monitor Accelerator Voltage

        returns:
            float
        """
        return '0.000'

    def MBC(self):
        """
        Monitor Beam Current

        Returns float
        """
        return '0.000'

    def MEI(self):
        """
        Unknown command
        :return:
        """
        return '27.0'

    def MF1(self):
        """
        Monitor Fault Analysis word 1
        """
        return '0'

    def MF2(self):
        """
        Monitor Fault Analysis word 2
        """
        return '0'

    def MF3(self):
        """
        Monitor Fault Analysis word 3
        """
        return '0'

    def MF4(self):
        """
        Monitor Fault Analysis word 4
        """
        return '0'

    def MF5(self):
        """
        Monitor Fault Analysis word 5
        """
        return '0'

    def MF6(self):
        """
        Monitor Fault Analysis word 6
        """
        return '0'

    def MFA(self):
        """
        Monitor Fault Analysis
        """
        return '0x0000 0x0000 0x0000 0x0000 0x0000 0x0000'

    def MFG(self):
        """
        """
        if self.faults:
            return '1'
        else:
            return '0'

    def MH(self):
        """
        Monitor Hours

        Returns float
        """
        return f'{self.run_hours}'

    def MP(self):
        return f'{self.current_state}'

    def MRC(self):
        """
        Monitor Reservoir Current

        returns:
            float
        """
        return '0.000'

    def MTC(self):
        """
        Monitor Temperature Controller
        :return:
        """
        return f'{self.board_temp}'

    def MTP(self):
        """
        Monitor Tube Temperature
        :return:
        """
        return f'{self.tube_pres}'

    def MTT(self):
        """
        Monitor Tube Temperature
        :return:
        """
        return f'{self.tube_temp}'

    def Q(self):
        """
        Quit (emergency shutdown - generate a fault)
        :return:
        """
        self.faults = True
        self.current_state = 32
        return '0'

    def RCAT(self):
        """

        :return:
        """
        return f'TUBE{self.tube_str}'

    def RP1D(self):
        return f'{self.pulse1_delay}'

    def RP1W(self):
        return f'{self.pulse1_width}'

    def RPD(self):
        return f'{self.duty_factor}'

    def RPF(self):
        return f'{self.pulse_freq}'

    def SBV(self):
        self.beam_value = int(self.msg_list.pop(0))
        # Do something with parm to affect simulation
        return '0'

    def SUT(self):
        """
        Sets the auto shut down time (if enabled) in seconds.
        """
        parm = self.msg_list.pop(0)
        # Do something with parm to affect simulation
        return '0'

    def U(self):
        """
        User mode
        """
        if self.msg_list.pop(0) == 'TMFP':
            return '1'
        else:
            return '0'


