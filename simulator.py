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

    def __init__(self, gen_type='MINI', tube_str='235DT'):
        self.gen_type = gen_type
        self.tube_str = tube_str

    def exec_func(self, inst_str):
        func = getattr(self, inst_str)
        return func()

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
            seq, msg = strip_msg(data)
            # print(f'{addr[0]} sent msg: {data} extracted to: {msg} with seq: {seq}')
            print(f'Received : {seq} : {msg}')
            # print(f'msg checksum = {generate_checksum(seq+msg)}')
            time.sleep(0.05)  # Delay response from command just a bit
            for submsg in msg:
                self.exec_func(msg.pop(0))


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