class GenSimulator:
    """
    Generator simulator class
    """
    # default port assignments
    gen_inp_port = 55556
    gen_out_port = 55555

    debug = False

    def __init__(self, gen_type='MINI', tube_str='235DT', gen_ip_num='192.168.1.121'):
        self.gen_type = gen_type
        self.tube_str = tube_str
        self.gen_ip_num = gen_ip_num

        # Below attributes correspond to device parameters
        self.accel_current = 0.0
        self.accel_voltage = 0.0
        self.amp_hours = 0
        self.board_temp = 28
        self.system_state = 32
        self.fault_1 = 0x02  # External interlock fault
        self.fault_2 = 0x00
        self.fault_3 = 0x00
        self.fault_4 = 0x00
        self.fault_5 = 0x00
        self.fault_6 = 0x00
        self.getter_current = 0.0
        self.getter_voltage = 4.0
        self.high_voltage = 0
        self.input_emf = 26
        self.pulse_duty_cycle = 20
        self.pulse_freq = 5000
        self.pulse_width = 0
        self.pulse1_delay = 0
        self.pulse1_width = 45
        self.pulse2_delay = 0
        self.pulse2_width = 0
        self.pulse3_delay = 0
        self.pulse3_width = 0
        self.run_seconds = 0
        self.source_voltage = 2000
        self.shutdown_time = 0
        self.system_locked = True
        self.tube_pres = 120
        self.tube_temp = 26
        self.host_interlock_char = '!'
        self.serial_interlock_enabled = False

        # Device constants
        if gen_type == 'MINI':
            self.MAX_ACCEL_CURRENT = 70
            self.MIN_ACCEL_CURRENT = 20
            self.MAX_PULSE_FREQ = 20000
            self.MIN_PULSE_FREQ = 250
        else:
            self.MAX_ACCEL_CURRENT = 100
            self.MIN_ACCEL_CURRENT = 0
            self.MAX_PULSE_FREQ = 10000
            self.MIN_PULSE_FREQ = 1000
        # System states
        self.SYSTEM_STATE_INIT = 0x0001
        self.SYSTEM_STATE_RSV1 = 0x0002
        self.SYSTEM_STATE_RSV2 = 0x0004
        self.SYSTEM_STATE_STANDBY = 0x0008
        self.SYSTEM_STATE_RUNNING = 0x0010
        self.SYSTEM_STATE_FAULTED = 0x0020
        self.SYSTEM_STATE_SSHV = 0x0040
        self.SYSTEM_STATE_MCHG = 0x0080
        self.SYSTEM_STATE_IDLE = 0x0100
        self.SYSTEM_STATE_LAMP = 0x0200
        self.SYSTEM_STATE_BMST = 0x0400
        self.SYSTEM_STATE_SSBM = 0x0800
        self.SYSTEM_STATE_SSBH = 0x1000
        self.SYSTEM_STATE_SDBM = 0x2000
        self.SYSTEM_STATE_SDHV = 0x4000
        self.SYSTEM_STATE_TEST = 0x8000
        # quiescent / transient values
        self.IDEAL_TUBE_PRES = 120.003
        self.IDEAL_TUBE_TEMP = 36.0
        self.IDEAL_INPUT_EMF = 24.0
        self.IDEAL_BOARD_TEMP = 39.0

        self.GETTER_IDLE = 1.5
        self.GETTER_RAMP = 2.6
        self.GETTER_RUNNING = 1.8
        self.ACCEL_VOLTAGE_WARM = 60
        self.NEUTRONS_RAMP_TIME = 10
        self.ACCEL_CURRENT_NOISE = 4
        self.ACCEL_VOLTAGE_NOISE = 2
        self.GETTER_CURRENT_NOISE = 0.1
        self.ENV_NOISE = 0.5

        # Simulator specific attributes
        self.sim_timer = 0
        self.response_delay = 100000    # Delay time in microseconds
        self.faults = True
        self.msg_list = []
        self.neutrons_on = False
        self.neutrons_starting = False
        self.neutrons_ramping_up = False
        self.neutrons_ramping_down = False
        self.neutrons_start_time = 0
        self.accel_voltage_sp = 0
        self.accel_voltage_set = 0
        self.accel_current_sp = 0
        self.accel_current_set = 0
        self.getter_current_sp = 0
        self.accel_voltage_ramping = False
        self.accel_current_ramping = False
        self.getter_current_ramping = False
        self.start_time = 0
        self.orig_seconds = self.run_seconds
        self.socket_timeout = 2.0

        # NULL cmd flags
        self.nulls = {}

        def mf_method_factory(name, i):
            """
            Factory method to create class (M)onitor (F)ault methods when instantiated.
            :param name: Name to give the instantiated method
            :param i: Fault word number
            :return: Entrypoint to instantiated method
            """
            def MFn_template():
                """
                Command: Monitor Fault word n
                Function: Returns the fault status word.
                Details: This command returns the specific bitmapped decimal fault word (16 bits),
                corresponding to fault word n. See generator documentation for details on fault words
                :return: (int) a
                """
                MFn_template.__name__ = name
                try:
                    return str(getattr(self, f'fault_{i}'))
                except Exception as e:
                    print(f'Exception in generated function : {name}')
                    raise e
            return MFn_template

        def rp_method_factory(name, i, p):
            """
            Factory method to create (R)ead (P)ulse methods when instantiated.
            :param name: Name to give the instantiated method
            :param i: Pulse number (int)
            :param p: Parameter type (D)elay or (W)idth
            :return: Entrypoint to instantiated method
            """

            def RPnp_template():
                """
                Command: Read Pulse n Delay / Width
                Function: Sets the pulse n delay or width in microseconds.
                Details: This command allows the user to set the pulse n delay or width.
                No bounds checking is done.
                Inputs: xxx
                :return:
                   xxx.xxx (?????)
                """
                RPnp_template.__name__ = name
                if p == 'D':
                    try:
                        return str(getattr(self, f'pulse{i}_delay'))
                    except Exception as e:
                        print(f'Exception in generated function : {name}')
                        raise e
                else:
                    try:
                        return str(getattr(self, f'pulse{i}_width'))
                    except Exception as e:
                        print(f'Exception in generated function : {name}')
                        raise e

            return RPnp_template

        def sp_method_factory(name, i, p):
            """
            Factory method to create (S)et (P)ulse methods when instantiated.
            :param name: Name to give the instantiated method
            :param i: Pulse number (int)
            :param p: Parameter type (D)elay or (W)idth
            :return: Entrypoint to instantiated method
            """

            def SPnp_template():
                """
                Command: Set Pulse n Delay / Width
                Function: Sets the pulse n delay or width in microseconds.
                Details: This command allows the user to set the pulse n delay or width.
                No bounds checking is done.
                Inputs: xxx
                :return:
                   xxx.xxx (?????)
                """
                SPnp_template.__name__ = name
                try:
                    if p == 'D':
                        val = float(self.msg_list.pop(0))
                        setattr(self, f'pulse{i}_delay', val)
                    else:
                        val = float(self.msg_list.pop(0))
                        setattr(self, f'pulse{i}_width', val)
                    return str(val)
                except Exception as e:
                    print(f'Exception in generated function : {name}')
                    raise e
            return SPnp_template

        # Create methods based on factory templates
        # Pulse methods (RP, SP)
        for i in range(1, 4):
            for t in ['SP', 'RP']:
                for p in 'DW':
                    name = f'{t}{i}{p}'
                    setattr(self, name, eval(f'{t.lower()}_method_factory(name, i, p)'))

        # Fault methods (MF)
        for i in range(1, 7):
            name = f'MF{i}'
            setattr(self, name, mf_method_factory(name, i))

        try:
            f = open(f'{self.tube_str}_info.txt', 'r')
            nfo = f.readline().split()
            self.run_seconds = self.orig_seconds = int(nfo[0])
            self.amp_hours = int(nfo[1])
            print(f'Generator info found for tube {self.tube_str}: {self.run_seconds} , '
                  f'{self.amp_hours}')
            f.close()
        except FileNotFoundError:
            f = open(f'{self.tube_str}_info.txt', 'w')
            f.write(f'{self.run_seconds} {self.amp_hours}')
            f.close()

    def analog_noise(self, noise):
        """
        :param noise: float (magnitude of random change)
        :return: float (input value with noise applied)
        """
        import random
        random.seed()

        return random.random() * noise

    def exec_func(self):
        """
        Description: Utilizing msg_list stack, pop off first element and return reference to corresponding method
        :return: function (reference)
        """
        cmd = self.msg_list.pop(0)
        # Check to see if this command is being voided via the simulator controller
        if self.nulls.get(cmd, 0) != 0:
            if self.nulls[cmd] > 0:
                self.nulls[cmd] -= 1
            self.msg_list.insert(0, cmd)    # Put name of command onto msg_list for use in send_null method
            func = getattr(self, 'send_null')
            return func()
        try:
            func = getattr(self, cmd)
        except AttributeError:
            print(f'Generator simulation: unknown message received: {cmd}')
            func = getattr(self, 'null_cmd')
        return func()

    def run_simulation(self):
        """
        description: Main simulation engine. Accepts and responds to UDP commands and affects simulation parameters.
        :return: n/a
        """
        import re
        import socket
        import time
        import threading

        resp_list = []
        sock_timeout = self.socket_timeout

        in_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # in_sock.settimeout(sock_timeout)     # How long to wait for a message before exception
        out_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        in_sock.bind((self.gen_ip_num, self.gen_inp_port))

        def strip_msg(bdata):
            sdata = bdata.decode('UTF-8')
            pat = re.compile('\$[a-z](.+?)#')  # Match all characters between $? and #
            m = pat.match(sdata)
            return m.group(0)[1], m.group(1).split()

        def send_msg(message, addr, seq):
            chk = generate_checksum(seq + ' ' + message)
            respstr = f'{seq} {message}#{chk[2:].zfill(2)}\r'
            # respstr = f'{seq}{message}#{chk}\r\x00'
            respbytes = respstr.encode('utf-8')  # Convert string to byte object
            if self.debug:
                print(f'Sending {respbytes} to {addr}')
            out_sock.sendto(respbytes, (addr, self.gen_out_port))

        def generate_checksum(message):
            s = 0
            for i in range(len(message)):
                s += ord(message[i])
            return hex(~s & 0xff).upper()   # Mask to one byte, invert and return
                                            # Using uppercase to deal with strange client requirement

        def threaded_simulator(shutdown):
            while not shutdown.is_set():
                self.svc_gen_state()
                self.svc_accel_voltage()
                self.svc_accel_current()
                self.svc_getter_current()
                self.svc_environment()
            return

        shutdown_event = threading.Event()
        t = threading.Thread(target=threaded_simulator, args=(shutdown_event,))
        print(f'Starting simulator thread')
        t.start()

        while True:
            try:
                data, addr = in_sock.recvfrom(1024)  # Will wait for socket.timeout before throwing exception
                seq, self.msg_list = strip_msg(data)
                if self.debug:
                    print(f'Received : {seq} : {self.msg_list} extracted from {data}')
                resp_list.clear()
                while len(self.msg_list) > 0:
                    resp_list.append(self.exec_func())
                resp = ' '.join(resp_list)
                # Throttle our responses a bit
                time.sleep(self.response_delay / 1e6)
                send_msg(resp, addr[0], seq)
            except socket.timeout:
                print(f'[{time.strftime("%H:%M:%S",time.localtime())}] UDP receive timeout')

        shutdown_event.set()


    def svc_gen_state(self):
        """
        Description: Main state-machine for simulation.
        :return:
        """
        import time

        self.check_system_state()

        if self.system_state & self.SYSTEM_STATE_FAULTED == self.SYSTEM_STATE_FAULTED:
            self.neutrons_starting = self.neutrons_ramping_up = self.neutrons_on = False
            return
        if self.neutrons_starting:
            self.system_state = self.SYSTEM_STATE_SSHV  # Soft beam start
            self.getter_current_sp = self.GETTER_RAMP
            self.accel_voltage_sp = self.ACCEL_VOLTAGE_WARM
            self.neutrons_start_time = time.time()
            self.neutrons_starting = False
            self.neutrons_ramping_up = True
            return
        if self.neutrons_ramping_up and (time.time() - self.neutrons_start_time) > self.NEUTRONS_RAMP_TIME:
            self.system_state = self.SYSTEM_STATE_RUNNING
            self.getter_current_sp = self.GETTER_RAMP
            self.neutrons_ramping_up = False
            self.neutrons_on = True
            self.start_time = int(time.time())
            return
        if self.neutrons_on:
            self.accel_voltage_sp = self.accel_voltage_set
            self.accel_current_sp = self.accel_current_set
            self.getter_current_sp = self.GETTER_RUNNING
            if self.neutrons_ramping_down:
                self.system_state = self.SYSTEM_STATE_SDHV
                self.getter_current_sp = self.GETTER_IDLE
                self.accel_voltage_sp = 0
                self.accel_current_sp = 0
                self.neutrons_on = False
            return
        if self.neutrons_ramping_down and self.accel_current < 0.5:
            self.system_state = self.SYSTEM_STATE_IDLE
            self.neutrons_ramping_down = False
            return
        if self.faults:
            self.system_state = self.SYSTEM_STATE_FAULTED
            return
        if not self.neutrons_ramping_up and not self.neutrons_ramping_down:
            self.system_state = self.SYSTEM_STATE_IDLE
            self.getter_current_sp = self.GETTER_IDLE
        if self.system_state != self.SYSTEM_STATE_RUNNING:
            if self.run_seconds != self.orig_seconds:
                f = open(f'{self.tube_str}_info.txt', 'w')
                f.write(f'{self.run_seconds} {self.amp_hours}')
                f.close()
                self.orig_seconds = self.run_seconds
        return
    
    def svc_accel_current(self):
        """
        Description: Services the accelerator current parameter
        :return:
        """
        if self.accel_current > self.accel_current_sp:
            self.accel_current -= self.analog_noise(self.ACCEL_CURRENT_NOISE)
        else:
            self.accel_current += self.analog_noise(self.ACCEL_CURRENT_NOISE)
        if self.accel_current_sp == 0 and self.accel_current < 5:
            self.accel_current = 0
        return

    def svc_accel_voltage(self):
        """
        Description: Services the accelerator voltage parameter
        :return:
        """
        if self.accel_voltage_ramping:
            self.accel_voltage += self.analog_noise(5)
            if abs(self.accel_voltage_sp - self.accel_voltage < 6):
                self.accel_voltage_ramping = False
        elif self.accel_voltage > self.accel_voltage_sp:
            self.accel_voltage -= self.analog_noise(self.ACCEL_VOLTAGE_NOISE)
        else:
            self.accel_voltage += self.analog_noise(self.ACCEL_VOLTAGE_NOISE)
        if self.accel_voltage_sp == 0 and self.accel_voltage < 5:
            self.accel_voltage = 0
        return

    def svc_getter_current(self):
        """
        Description: Services the getter current parameter
        :return:
        """
        if self.getter_current_sp == 0:
            return
        if self.system_state == self.SYSTEM_STATE_RUNNING:
            if self.getter_current > self.getter_current_sp:
                self.getter_current -= self.analog_noise(self.GETTER_CURRENT_NOISE)  # Wiggle the value a little
            else:
                self.getter_current += self.analog_noise(self.GETTER_CURRENT_NOISE)  # Wiggle the value a little
        else:
            if self.getter_current > self.getter_current_sp:
                self.getter_current -= abs(self.getter_current_sp - self.getter_current) * .001
                #self.getter_current -= self.analog_noise(self.GETTER_CURRENT_NOISE*.5)  # Wiggle the value a little
            else:
                self.getter_current += abs(self.getter_current_sp - self.getter_current) * .001
                #self.getter_current += self.analog_noise(self.GETTER_CURRENT_NOISE*.5)  # Wiggle the value a little
        return

    def svc_environment(self):
        """
        Description: Services the generator environmental parameters
        :return:
        """
        import time

        # Vary the parameters a bit somewhat randomly
        for parm in ['IDEAL_BOARD_TEMP', 'IDEAL_TUBE_PRES', 'IDEAL_TUBE_TEMP', 'IDEAL_INPUT_EMF']:
            # Not crazy about hard-coding these constants like this^^
            sp = float(getattr(self, parm))
            curr_val = float(getattr(self, parm[6:].lower()))
            if self.analog_noise(1) > 0.8:  # Don't update values at every iteration
                if curr_val > sp:
                    setattr(self, parm[6:].lower(), curr_val - self.analog_noise(self.ENV_NOISE))
                else:
                    setattr(self, parm[6:].lower(), curr_val + self.analog_noise(self.ENV_NOISE))
        if (self.system_state == self.SYSTEM_STATE_RUNNING) & (time.time() > self.start_time):
            self.run_seconds += int(time.time()) - self.start_time
            self.amp_hours += int((int(time.time()) - self.start_time) * self.accel_current)
            self.start_time = int(time.time())

    def check_system_state(self):
        """
        Description: Checks for any faults and adjusts system state accordingly
        """
        if self.fault_1 + self.fault_2 + self.fault_3 + self.fault_4 + self.fault_5 + self.fault_6 > 0:
            self.faults = True  # This should be set by a separate fault monitoring task
            self.system_state = self.SYSTEM_STATE_FAULTED  # This should be set by a separate fault monitoring task
            self.accel_current = self.accel_current_sp = 0
            self.accel_voltage = self.accel_voltage_sp = 0
            self.getter_current_sp = self.getter_current = 0

    def null_cmd(self):
        """
        Entrypoint for all unknown commands

        :return: 0
        """
        return '0'

    def send_null(self):
        """
        Method to return NULL character

        :return: \00
        """
        print(f'NULL being returned in response to cmd : {self.msg_list.pop(0)}')
        return '\00'    # Null

    def C(self):
        """
        Command: Clear
        Function: Clears all of the current fault conditions.

        :return: 0
        """
        self.faults = False
        self.system_state = self.SYSTEM_STATE_IDLE
        self.fault_1 = 0
        return '0'

    def IC(self):       # Check via packet capture
        """
        Command: Interlock Character
        Function: Receives the interlock character that keeps the serial port
        interlock enabled.
        Input : '[ (host interlock character)'
        Details: This command receives the interlock character. Once the
        interlock character is received, the interlock timeout is reset to
        16 seconds. If the interlock character is not received (via the
        “IC [” command from the remote system) within 16 seconds
        of the interlock being enabled, the system will time out and
        the interlock will open, initiating a fault condition. Also, the
        remote system processor must respond with a “]” or it will
        time out. Printable ASCII characters are used to facilitate
        testing and debugging. Once the interlock is opened after
        being enabled, it can only be re-enabled by entering the
        “IR<rcode>” command or cycling power to the system.

        :return: '] (remote interlock character)'
        """
        val = self.msg_list.pop(0)
        if val != '[':
            print(f'In IC function, expected \'[\' but found \'{val}\'')
            self.msg_list.pop(0)    # Flush out character from cmd stack
        else:
            self.host_interlock_char = self.msg_list.pop(0)
        return f'] {self.host_interlock_char}'

    def IE(self):
        """
        Command: Interlock Enable
        Function: Enables the serial port interlock circuit.
        Details: This command enables the serial port interlock. Once
        enabled, the interlock is made for 16 seconds. If the interlock
        character is not received (via the “IC [” command) at least
        once every two seconds from that time on, the system will
        time out and the interlock will open, generating a fault. Once
        the interlock has been opened after being enabled, it can only
        be re-enabled by cycling power to the system or entering the
        “IR<rcode>” command.

        :return: '0'  ok
        """
        self.serial_interlock_enabled = True
        return '0'

    def IM(self):
        """
        Command: Idle Mode
        Returns: 0 or 2
        Function: Puts the system in idle mode.
        Details: This command is identical to entering the “N 0” command.
        The system initiates an orderly shut down and returns to the
        idle mode.

        :return:
            '0'  ok
            '2'  fault
        """
        # check for valid entry?
        # Set mode to "HV start / Soft start"
        # Ramp up the voltage
        self.neutrons_ramping_down = True
        return '0'

    def IN(self):       # Check via packet capture
        """
        Command: Idle Normal
        Returns: 0, 1 or 2
        Function: Puts the system in idle mode.
        Details: This command restarts the ion source and allows neutron
        production to restart quickly from standby mode. This
        command is only valid if the system is in standby mode

        :return:
            '0' ok
            '1' illegal transition from current state
            '2' fault
        """

        self.neutrons_ramping_down = True
        return '0'

    def IR(self):  # Check via packet capture
        """
        Command: Interlock Reset
        Function: Disables and resets the serial port interlock circuit.
        Input : '<PASSWORD>'
        Details: This command disables the serial port interlock, removes any
        high voltage at the tube, and resets the enable for the serial
        port interlock. The purpose of this command is to allow a
        reset of the serial port interlock without cycling power to the
        system. Once this command is entered, the “IE” command
        will need to be executed to re-enable the serial port interlock.
        The faults will then need to be cleared and the interlock
        character (“IC [”) provided in order to operate the system.
        The passcode is available from Thermo and may change with
        revisions.

        :return:
            '0'
        """
        val = self.msg_list.pop(0)
        # Do something with this val to verify proper password??
        return '0'

    def IS(self):  # Check via packet capture
        """
        Command: Idle Standby
        Returns: 0, 1 or 2
        Function: Puts the system in standby mode.
        Details: This command removes the voltage from the ion source and
        will maintain the reservoir current at the system value needed
        to maintain the beam current set by the user. It will also leave
        the high voltage at the user configured setpoint. The system
        will still produce a small number of neutrons. This command
        allows the system to be restarted quickly. This command is
        only valid if the system is in the RUNNING state.

        :return:
            '0' ok
            '1' illegal transition from current state
            '2' fault
        """
        self.neutrons_ramping_down = True
        return '0'

    def MAC(self):
        """
        Command: Monitor Accelerator Current
        Function: Returns the current reading of the average accelerator
        current in microamperes

        :return: self.accel_current
        """
        return f'{self.accel_current:.2f}'

    def MAH(self):
        """
        Command: Monitor Amp-Hours
        Function: Returns the current micro-amp-hr total of the neutron tube.

        :return:
            self.amp_hours
        """
        return f'{self.amp_hours:.3f}'

    def MAV(self):
        """
        Command: Monitor Accelerator Voltage
        Function: Returns the current voltage reading of the HVPS in kilovolts.

        :return:
            self.accel_voltage
        """
        return f'{self.accel_voltage:.1f}'

    def MBC(self):
        """
        Command: Monitor Beam Current
        Function: Returns the current reading of the average accelerator
        current in microamperes

        :return:
            self.accel_current
        """
        return f'{self.accel_current:.2f}'

    def MEI(self):
        """
        Command: Monitor EMF Input
        Function: Returns the input voltage to the generator electronics (nominal 24V).

        :return:
            self.input_emf
        """
        return f'{self.input_emf:.1f}'

    def MFA(self):
        """
        Command: Monitor Fault Analysis
        Function: Returns the 6 bytes containing the fault status.
        Details: This command returns the 6 bitmapped hexadecimal fault
        words (16 bits each), separated by spaces, containing the
        status of all of the system fault conditions. See generator documentation for details on fault words

        :return:
            0xfault_1 0xfault_2 0xfault_3 0xfault_4 0xfault_5 0xfault_6
        """
        f1str = f'0x{f"{self.fault_1:0x}".zfill(4)}'
        f2str = f'0x{f"{self.fault_2:0x}".zfill(4)}'
        f3str = f'0x{f"{self.fault_3:0x}".zfill(4)}'
        f4str = f'0x{f"{self.fault_4:0x}".zfill(4)}'
        f5str = f'0x{f"{self.fault_5:0x}".zfill(4)}'
        f6str = f'0x{f"{self.fault_6:0x}".zfill(4)}'
        return f'{f1str} {f2str} {f3str} {f4str} {f5str} {f6str}'

    def MFG(self):
        """
        Command: Monitor Fault Global
        Function: Returns a value to indicate if any faults have occurred.

        :return:
            '0' if no faults, '1' if any faults
        """
        if self.faults:
            return '1'
        else:
            return '0'

    def MH(self):
        """
        Command: Monitor Hours
        Function: Returns the amount of time the neutron tube has spent in the
        running state in seconds.

        :return:
            self.run_seconds
        """
        return f'{self.run_seconds}'

    def MI(self):
        """
        Command: Monitor Interlock
        Function: Displays the status of the interlocks.
        Details: This command displays whether the pressure switch,
        electrical switch and serial port interlocks are open or closed.
        This command differs from the “MFA” command in that it
        will display if the serial port interlock is bypassed and if the
        gas pressure is low even though the interlock is closed. In
        computer mode, a bitmapped hexadecimal byte is returned. If
        a “0” is read, all of the interlocks are closed; if anything other
        than a “0” is read, one or more of the interlocks is open. The
        bitmapping for the first three bits is the same as the first byte
        in the fault status, but it only contains the interlock.
        Therefore, bit 0 is the pressure switch interlock; bit 1 is the
        electrical switch interlock; and bit 2 is the serial port
        interlock.
        0 Relay Interlock (0 = closed) (HVPS Power)
        1 User Interlock Status (0 = closed)
        2 Serial Interlock Status (0 = closed)
        3 Serial Interlock Bypassed
        4 Reserved
        5 Reserved
        6 Reserved
        7 Reserved
        8 Reserved

        :return:
            (hex) aa
        """
        print('Warning - MI not implemented properly yet')
        return f'0x00'

    def MP(self):
        """
        Command: Monitor Process
        Function: Returns the current state of the system in decimal.
        Details: This command displays the current state of the system on the
        DNC board. Please refer to Table 5-13, System States, for the
        list of possible system states, which are bitmapped.

        :return:
            self.system_state
        """
        return f'{self.system_state}'

    def MRC(self):
        """
        Command: Monitor Reservoir Current
        Function: Returns the reading of the reservoir current in amperes.

        :return:
            self.getter_current
        """
        return f'{self.getter_current:.1f}'

    def MRR(self):
        """
        Command: Monitor Reservoir Resistance
        Function: Returns the calculated resistance of the getter

        :return:
            self.getter_voltage / self.getter_current
        """
        try:
            val = self.getter_voltage / self.getter_current
        except ZeroDivisionError:
            val = 999999
        return f'{val:.1f}'

    def MRV(self):
        """
        Command: Monitor Reservoir Voltage

        :return:
            self.getter_voltage
        """
        return f'{self.getter_voltage:.1f}'

    def MSV(self):
        """
        Command: Monitor Source Voltage

        :return:
            self.source_voltage
        """
        return f'{self.source_voltage:.1f}'

    def MTC(self):
        """
        Command: Monitor Temperature Controller
        Function: Returns the current reading of the controller board
        temperature in Celsius.

        :return:
            self.board_temp
        """
        return f'{self.board_temp:.2f}'

    def MTD(self):
        """
        Command: Monitor Tube Density

        :return:
            xxx.x
        """
        print('MTD not implemented yet')
        return '1'

    def MTP(self):
        """
        Command: Monitor Tube Pressure
        Function: Returns the current reading of the neutron tube pressure in
        pounds per square inch (psi).

        :return:
            self.tube_pres
        """
        return f'{self.tube_pres:.1f}'

    def MTS(self):
        """
        Command: Monitor Temperature Source

        :return:
            xxx.x
        """
        print('MTS not implemented yet')
        return f'{self.board_temp:.1f}'

    def MTT(self):
        """
        Command: Monitor Temperature Tube

        Function: Returns the current reading of the accelerator assembly
        temperature in Celsius.

        :return:
            self.tube_temp
        """
        return f'{self.tube_temp:.2f}'

    def N(self):
        """
        Command: Neutrons xx.xx
        Inputs: xx (setting of the HVPS)
        Function: This command initiates a start-up the system and slowly
        ramps up the high voltage to the specified value (in
        kilovolts). It will also stop the system if a number is set
        below a pre-programmed threshold (typically 60 kV);
        therefore, the system will shut down if “N=0” is entered.
        Details: Since the neutron output is exponentially related to the value
        of the high voltage, this is the primary value used to
        determine the neutron output (changes in the beam current
        will allow small changes to neutron output). When this value
        is set, the system will slowly ramp up the high voltage and
        beam current to the specified values. It will typically take
        between 30 seconds and one minute for the tube to ramp up to
        the high voltage and beam current before it will make a
        significant number of neutrons after this value is set. If there
        is a fault condition in the system, it must be cleared before
        this command is effective. This value is typically set to
        between 70 and 90 kV.

        :return:
            '0'  ok
            '1'  out of range
            '2'  fault
        """
        # check for valid entry?
        # Set mode to "HV start / Soft start"
        # Ramp up the voltage
        val = float(self.msg_list.pop(0))
        self.accel_voltage_set = val
        self.accel_voltage_ramping = True
        if not self.neutrons_on:
            self.neutrons_starting = True
        return '0'

    def Q(self):
        """
        Command: Quit
        Function: Initiates a hard shut down of the neutron tube (i.e., user
        generated fault).
        Details: This command shuts down the neutron tube as quickly as
        possible. This is different than the normal shut down using
        the “N=0” or “IM” commands in that it will not shut down in
        an orderly fashion. When this command is used, all voltages
        and currents will be set to zero and the condition of the
        system will not return to the idle state until power is cycled to
        the system or the user generated fault is cleared by entering
        the “C” command.

        :return:
            0
        """
        self.faults = True         # This should be set by a separate fault monitoring task
        self.system_state = self.SYSTEM_STATE_FAULTED     # This should be set by a separate fault monitoring task
        self.accel_current = self.accel_current_sp = 0
        self.accel_voltage = self.accel_voltage_sp = 0
        self.getter_current_sp = self.getter_current = 0
        self.fault_1 = self.fault_1 | 0x80
        return '0'

    def RBV(self):
        """
        Command: Read Beam Value

        :return:

        """
        print('RBV not implemented yet')
        return f'TUBE{self.accel_current}'

    def RCAR(self):     # Check against packet logs
        """
        Command: Returns the current revision of the HVPS.

        :return:
            self.tube_str
        """
        print('RCAR not implemented yet')
        return f'TUBE{self.tube_str}'

    def RCDA(self):
        print('RCDA not implemted yet')
        return 'NA'

    def RCDR(self):
        print('RCDR not implemted yet')
        return 'NA'

    def RCFR(self):
        print('RCFR not implemented yet')
        return 'NA'

    def RCXR(self):
        print('RCXR not implemented yet')
        return 'NA'

    def RCAT(self):
        """
        Command: Read Configuration Accelerator Tube
        Function: Returns the serial number of the current tube in the
        accelerator.

        :return:
            self.tube_str
        """
        return f'TUBE{self.tube_str}'

    def REA(self):
        print('REA not implemented yet')
        return 'na'

    def REM(self):
        print('REM not implemented yet')
        return 'na'

    def RPD(self):
        """
        Command: Read Pulse Duty

        Function: Returns the current setting of the source pulse duty cycle in
        percent.

        Details: This command displays the current setting of the duty cycle
        of the main source pulse. The duty cycle will be changed if
        the pulse width is changed based on the current frequency
        setting. The resolution will vary depending on the frequency.
        The duty cycle can be set from 0 to 100% in 1% increments.

        Attribute: pulse_duty_cycle

        :return:
            xx.xxx
        """
        return f'{self.pulse_duty_cycle:.3f}'

    def RPF(self):
        """
        Command: Read Pulse Frequency

        Function: Returns the current setting of the source pulse frequency in
        Hz.

        Details: This command displays the current setting of the frequency
        of the main source pulse. The duty cycle will be changed if
        the pulse width is changed based on the current frequency
        setting. The resolution will vary depending on the frequency.
        The duty cycle can be set from 0 to 100% in 1% increments.

        Attribute: pulse_freq

        :return:
            xxxxx
        """
        return f'{self.pulse_freq}'

    def RUC(self):
        print('RUC not implemented yet')
        return 'NA'

    def RUM(self):
        print('RUM not implemented yet')
        return 'NA'

    def RUT(self):
        print('RUT not implemented yet')
        return 'NA'

    def RZTC(self):
        print('RZTC not implemented yet')
        return 'NA'

    def SBV(self):
        """
        Command: Set Beam Value

        Inputs: xx.xx

        Function: Sets the system value of the beam current in microamps.

        Details: This command allows the user to set the value of the beam
        current. This value is typically set to between 20 and 70 microamps.

        Attribute: accel_current_sp

        :return:
            '0' (cmd OK)
            '1' (cmd invalid / out of range)
        """
        val = float(self.msg_list.pop(0))
        if self.MIN_ACCEL_CURRENT < val < self.MAX_ACCEL_CURRENT:
            self.accel_current_set = val
            return '0'
        else:
            return '1'

    def SCDA(self):
        print('SCDA not implemented yet')
        return 'na'

    def SEA(self):
        print('SEA not implemented yet')
        return 'na'

    def SPD(self):
        """
        Command: Set Pulse Duty

        Function: Sets the source pulse duty factor to xx in %.

        Details: This command allows the user to set the source pulse duty
        cycle, which is the duty cycle of the main source pulse. The
        duty cycle will be changed if the pulse width is changed
        based on the current frequency setting. This command will
        change the current pulse width value. The resolution will
        vary depending on the frequency

        Inputs: xx

        Attribute: pulse_duty

        :return:
            '0' (cmd OK)
            '1' (cmd invalid / out of range)
        """
        val = float(self.msg_list.pop(0))
        if val == 100 or (20 <= val <= 50):
            self.pulse_duty_cycle = val
            return '0'
        else:
            # Invalid entry
            return '1'

    def SPF(self):
        """
        Command: Set Pulse Frequency

        Function: Sets the source pulse frequency to xxxxx in Hz.

        Details: This command allows the user to set the source pulse
        frequency. The resolution of this setting depends on the
        frequency being set. The frequency can be set from DC or
        250 Hz to 20 kHz.

        Inputs: xx.xx

        Attribute: pulse_frequency

        :return:
            '0' (cmd OK)
            '1' (cmd invalid / out of range)
        """
        val = float(self.msg_list.pop(0))
        if val == 0:
            # Setting to DC mode is valid
            self.pulse_freq = 0
            return '0'
        elif self.MIN_PULSE_FREQ < val < self.MAX_PULSE_FREQ:
            self.pulse_freq = val
            return '0'
        else:
            # Invalid entry
            return '1'

    def SUC(self):
        print('SUC not implemented yet')
        return 'na'

    def SUM(self):
        print('SUM not implemented yet')
        return 'na'

    def SUT(self):
        """
        Command: Set User Time

        Inputs: xxxxx

        Function: Sets the auto shut down time (if enabled) in seconds.

        Details: This command allows the user to set the auto shut down time
        if it has been enabled with the “SUM” command. Note that
        this is a password protected command and the system must be
        unlocked using the “U TMFP” command (where TMFP is
        the current user level password of the system). If this time is
        set to “0”, the system will run until the user shuts it down.

        Attribute: shutdown_time

        :return:
            '0'
        """

        self.shutdown_time = self.msg_list.pop(0)
        return '0'

    def SZTC(self):
        print('SZTC not implemented yet')
        return 'na'

    def U(self):
        """
        Command: Unlock

        Inputs: <code TMFP>
        Returns (Computer Mode): 0 or 1

        Function: Unlocks the system so that parameters can be set up.

        Details: This command allows the user to change parameters such as
        the frequency and the pulse width. If the system is not
        unlocked, the parameters can be read but not changed. The
        prompt will change in terminal mode indicating the state of
        the lock. The system will remain in setup mode until it is
        locked by entering the “U” command without parameters or a
        bad code.

        :return:
            '1' (system unlocked)
            '0' (system locked)
        """
        if self.msg_list.pop(0) == 'TMFP':
            self.system_locked = False
            return '1'
        else:
            self.system_locked = True
            return '0'


