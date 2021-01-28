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
        self.amp_hours = 0.0
        self.board_temp = 0.0
        self.system_state = 32
        self.fault_1 = 0x02  # External interlock fault
        self.fault_2 = 0x00
        self.fault_3 = 0x00
        self.fault_4 = 0x00
        self.fault_5 = 0x00
        self.fault_6 = 0x00
        self.getter_current = 0.0
        self.high_voltage = 0
        self.input_emf = 0.0
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
        self.shutdown_time = 0
        self.system_locked = True
        self.tube_pres = 0.0
        self.tube_temp = 0.0

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
        self.IDEAL_TUBE_TEMP = 21.99
        self.IDEAL_INPUT_EMF = 24.0
        self.IDEAL_BOARD_TEMP = 32.5

        self.GETTER_IDLE = 1.5
        self.GETTER_RAMP = 2.6
        self.GETTER_RUNNING = 1.8
        self.ACCEL_VOLTAGE_WARM = 60
        self.NEUTRONS_RAMP_TIME = 10
        self.ACCEL_CURRENT_NOISE = 4
        self.ACCEL_VOLTAGE_NOISE = 2
        self.GETTER_CURRENT_NOISE = 0.1
        self.ENV_NOISE = 0.1



        # Simulator specific attributes
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

                Attribute: fault_n

                :return:
                    (int) a
                """
                MFn_template.__name__ = name
                return str(getattr(self, f'fault_{i}'))
            return MFn_template

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

                Attribute: pulse1_delay

                :return:
                   xxx.xxx (?????)
                """
                SPnp_template.__name__ = name
                print(f'Inside {SPnp_template.__name__} with msg: {self.msg_list}')
                if p == 'D':
                    val = float(self.msg_list.pop())
                    setattr(self, f'pulse{i}_delay', val)
                else:
                # Something is very odd in the format of the message being sent here from the ANL client
                # So I'm pop(ing) the messages off from the back in here
                # This kind of breaks the model of being able to stack commands in one msg, so needs
                # to be addressed better.
                    val = float(self.msg_list.pop())
                    setattr(self, f'pulse{i}_width', val)
                return str(val)
            return SPnp_template

        # Create methods based on factory templates
        # SP methods
        for i in range(1, 4):
            for p in 'DW':
                name = f'SP{i}{p}'
                setattr(self, name, sp_method_factory(name, i, p))
        # MF methods
        for i in range(1, 7):
            name = f'MF{i}'
            setattr(self, name, mf_method_factory(name, i))

        # Check for saved attributes like hours (hobbs) and amp-hour values
        # If it does not exist, create with filename = tubestr_info.txt
        # If it does exist, read the startup values for hours and amp-hours


    def analog_noise(self, noise):
        """
        :param noise: float (magnitude of random change)
        :return: float (input value with noise applied)
        """
        import random
        random.seed()

        return random.random() * noise

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
            if self.debug:
                print(f'Received : {seq} : {self.msg_list}')
            #time.sleep(0.05)  # Delay response from command just a bit
            resp_list.clear()
            while len(self.msg_list) > 0:
                resp_list.append(self.exec_func())
            if len(resp_list) > 1:
                resp = ' '.join(resp_list)
            else:
                resp = resp_list[0]
            send_msg(resp, addr[0], seq)
            self.svc_gen_state()
            self.svc_accel_voltage()
            self.svc_accel_current()
            self.svc_getter_current()
            self.svc_environment()

    def svc_gen_state(self):
        import time

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

        return
    
    def svc_accel_current(self):
        if self.accel_current > self.accel_current_sp:
            self.accel_current -= self.analog_noise(self.ACCEL_CURRENT_NOISE)
        else:
            self.accel_current += self.analog_noise(self.ACCEL_CURRENT_NOISE)
        if self.accel_current_sp == 0 and self.accel_current < 5:
            self.accel_current = 0
        return

    def svc_accel_voltage(self):
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
        if self.getter_current_sp == 0:
            return
        if self.system_state == self.SYSTEM_STATE_RUNNING:
            if self.getter_current > self.getter_current_sp:
                self.getter_current -= self.analog_noise(self.GETTER_CURRENT_NOISE)  # Wiggle the value a little
            else:
                self.getter_current += self.analog_noise(self.GETTER_CURRENT_NOISE)  # Wiggle the value a little
        elif self.system_state == self.SYSTEM_STATE_IDLE:
            self.getter_current = self.getter_current_sp
        return

    def svc_environment(self):
        for parm in ['IDEAL_BOARD_TEMP', 'IDEAL_TUBE_PRES', 'IDEAL_TUBE_TEMP', 'IDEAL_INPUT_EMF']:
            # Not crazy about hard-coding these constants like this^^
            sp = float(getattr(self, parm))
            curr_val = float(getattr(self, parm[6:].lower()))
            if self.analog_noise(1) > 0.7:  # Don't update values at every iteration
                if curr_val > sp:
                    setattr(self, parm[6:].lower(), curr_val - self.analog_noise(self.ENV_NOISE))
                else:
                    setattr(self, parm[6:].lower(), curr_val + self.analog_noise(self.ENV_NOISE))
        # Check to see if generator is ON and if so, increment the hours and amp-hours attributes
        # Write this to a file upon going from RUN/ON mode to IDLE or FAULT(?)

    def check_system_state(self):
        """
        Table 5–6. System States
        Number State Meaning
        $0001 INIT State during boot up
        $0002 Reserved Reserved for expansion
        $0004 Reserved Reserved for expansion
        $0008 STANDBY System is in standby mode for quick restart to neutron production
        $0010 RUNNING System has met all criteria and is producing neutrons
        $0020 FAULTED There is a fault in the system that will not allow the system to run
        $0040 SSHV Soft Start High Voltage – system is starting high voltage supplies
        $0080 MCHG Mode Change
        $0100 IDLE System is in idle state – no faults – waiting for user command
        $0200 LAMP System is starting the safety lamp and waiting to make sure that it sees light and current
        $0400 BMST Beam Start – system is setting the reservoir current to a high value to kick start the beam current
        $0800 SSBM Soft Start Beam – system is starting the control loop to control the beam current with the reservoir
        $1000 SSBH Soft Start Beam Hot – system is starting the control loop to control the beam current with
            the reservoir from a standby state
        $2000 SDBM Soft Down Beam – system is shutting down beam current
        $4000 SDHV Soft Down High Voltage – system is shutting down the high voltage
        $8000 TEST Special test mode for internal use

        :return:
        """
        if self.fault_1 + self.fault_2 + self.fault_3 + self.fault_4 + self.fault_5 + self.fault_6 > 0:
            self.system_state = self.system_state | self.SYSTEM_STATE_FAULTED

    def null_cmd(self):
        """
        Entrypoint for all unknown commands

        :return:
            0
        """
        return '0'

    def C(self):
        """
        Command: Clear

        Function: Clears all of the current fault conditions.

        Details: This command allows the user to clear any faults that have
        occurred. If fault conditions that can be detected still exist,
        they will be checked the next time through the real time loop.
        This means that it may take 10 to 20 microseconds after the faults have
        been cleared to read any faults that may still exist.

        Attribute: faults, system_state

        :return:
            0
        """
        self.faults = False                             # This should be set by a supervisor function
        self.system_state = self.SYSTEM_STATE_IDLE      # This should be set by a supervisor function
        self.fault_1 = 0                                # This should be set by a supervisor function
        return '0'

    def IM(self):
        """
        Command: Idle Mode

        Returns (Computer Mode): 0 or 2

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

    def MAC(self):
        """
        Command: Monitor Accelerator Current

        Function: Returns the current reading of the average accelerator
        current in microamperes

        Details: This command returns the current reading of average
        accelerator current. This reading is made from the HVPS.
        The value while the system is running is typically 20 to
        70 microamps. Neutron tube life is proportional to the beam current
        required. This reading is identical to the beam current for the
        neutron tube and controller configuration.

        Attribute: accel_current

        :return:
            xxx.xx
        """
        return f'{self.accel_current:.2f}'

    def MAH(self):
        """
        Command: Monitor Amp-Hours

        Function: Returns the current micro-amp-hr total of the neutron tube.

        Details: This command returns the current total number of micro-amp-hrs the
        neutron tube has spent in the running state. This is a better
        number than total time because neutron tube life increases at
        lower beam currents.

        Attribute: amp_hours

        :return:
            xxx.xxx
        """
        return f'{self.amp_hours:.3f}'

    def MAV(self):
        """
        Command: Monitor Accelerator Voltage

        Function: Returns the current voltage reading of the HVPS in kilovolts.

        Details: This command returns the current voltage reading of the
        HVPS. When this value is set, it will take some time to ramp
        up to the value set. [If the voltage does not reach the preprogrammed
        threshold (typically 60 kV) the system will shut down.]

        Attribute: accel_voltage

        :return:
            xxx.x
        """
        return f'{self.accel_voltage:.1f}'

    def MBC(self):
        """
        Command: Monitor Beam Current

        Function: Returns the current reading of the average accelerator
        current in microamperes

        Details: This command returns the current reading of average
        accelerator current. This reading is made from the HVPS.
        The value while the system is running is typically 20 to
        70 microamps. Neutron tube life is proportional to the beam current
        required. This reading is identical to the accelerator current.

        Attribute: accel_current

        :return:
            xxx.xx

        Returns float
        """
        return f'{self.accel_current:.2f}'

    def MEI(self):
        """
        Command: Monitor EMF Input

        Function: Returns the input voltage to the generator electronics (nominal 24V).

        Attribute: input_emf

        :return:
            xxx.x
        """
        return f'{self.input_emf:.1f}'

    def MFA(self):
        """
        Command: Monitor Fault Analysis

        Function: Returns the 6 bytes containing the fault status.

        Details: This command returns the 6 bitmapped hexadecimal fault
        words (16 bits each), separated by spaces, containing the
        status of all of the system fault conditions. See generator documentation for details on fault words

        Attributes: fault_1, fault_2, fault_3, fault_4, fault_5, fault_6

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

        Details: This command allows the fault status to be easily monitored
        without requiring that all of the fault words be displayed all of
        the time. If there is a fault, the user must determine which
        fault condition(s) exist by entering the “MFA” command or
        by reading each individually bitmapped fault word. If a “0” is
        returned, there are no fault conditions in the system; if a “1”
        is returned, there are fault conditions in the system.

        :return:
            (int) a
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

        Details: This command returns the amount of time the neutron tube
        has spent in the running state. The time is logged for tube life
        only during the time the tube spends in the running state.
        Leading zeros are suppressed when the data is returned. This
        allows the user to determine if a tube is due for maintenance.

        Attribute: run_seconds

        :return:
            (int) a
        """
        return f'{self.run_seconds}'

    def MP(self):
        """
        Command: Monitor Process

        Function: Returns the current state of the system in decimal.

        Details: This command displays the current state of the system on the
        DNC board. Please refer to Table 5-13, System States, for the
        list of possible system states, which are bitmapped.

        Attribute: system_state

        :return:
            (int) a
        """
        return f'{self.system_state}'

    def MRC(self):
        """
        Command: Monitor Reservoir Current

        Function: Returns the current reading of the reservoir current in
        amperes.

        Details: This command displays the reading of the reservoir current.
        The reservoir (sometimes called the “filament” or “getter”)
        controls the beam current. There is a closed loop that controls
        the beam current by controlling the amount of reservoir
        current. When the tube is not running, the reservoir is in idle
        mode. In the idle mode, the reservoir is typically set to about
        0.5 A. In the running mode, the reservoir current will
        typically be in the range of 1 to 2.5 A.

        Attribute: getter_current

        :return:
            xx.x
        """
        return f'{self.getter_current:.1f}'

    def MTC(self):
        """
        Command: Monitor Temperature Controller

        Function: Returns the current reading of the controller board
        temperature in Celsius.

        Details: This command displays the current reading of the controller
        board temperatures.

        Attribute: board_temp

        :return:
            xx.xx
        """
        return f'{self.board_temp:.2f}'

    def MTP(self):
        """
        Command: Monitor Tube Pressure

        Function: Returns the current reading of the neutron tube pressure in
        pounds per square inch (psi).

        Details: This command displays the current reading of the neutron
        tube pressure.

        Attribute: tube_pres

        :return:
            xxx.x
        """
        return f'{self.tube_pres:.1f}'

    def MTT(self):
        """
        Command: Monitor Temperature Tube

        Function: Returns the current reading of the accelerator assembly
        temperature in Celsius.

        Details: This command displays the current reading of the neutron
        tube temperature.

        Attribute: tube_temp

        :return:
            xx.xx
        """
        return f'{self.tube_temp:.2f}'

    def N(self):
        """
        Command: Neutrons xx.xx

        Inputs: xx (setting of the HVPS)

        Returns (Terminal Mode): 
        
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
        
        Attributes: accel_voltage, neutrons_on
        
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

    def RCAT(self):
        """
        Command: Read Configuration Accelerator Tube

        Function: Returns the serial number of the current tube in the
        accelerator.

        Details: The command displays the tube serial number with an
        appended “DD” or “DT”. DD indicates a Deuterium only
        loaded tube (2.4MeV); DT indicates

        Attribute: tube_str

        :return:
            str
        """
        return f'TUBE{self.tube_str}'

    def RP1D(self):
        """
        Command: Read Pulse 1 Delay

        Function: Returns the current setting of the delay on the DELAY n
        pulse in microseconds.

        Details: This command displays current setting on the Delay 1 pulse.

        Attribute: pulse1_delay

        :return:
            xx.xxx
        """
        return f'{self.pulse1_delay:.3f}'

    def RP1W(self):
        """
        Command: Read Pulse 1 Width

        Function: Returns the current setting of the width on the DELAY n
        pulse in microseconds.

        Details: This command displays current setting on the Delay 1 width.

        Attribute: pulse1_width

        :return:
            xx.xxx
        """
        return f'{self.pulse1_width:.3f}'

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

    def SPD(self):
        """
        Command: Set Pulse Delay

        Function: Sets the source pulse delay to xx in %.

        Details: This command allows the user to set the source pulse duty
        cycle, which is the duty cycle of the main source pulse. The
        duty cycle will be changed if the pulse width is changed
        based on the current frequency setting. This command will
        change the current pulse width value. The resolution will
        vary depending on the frequency

        Inputs: xx

        Attribute: pulse_delay

        :return:
            '0' (cmd OK)
            '1' (cmd invalid / out of range)
        """
        val = float(self.msg_list.pop(0))
        if val == 100 or (20 <= val <= 50):
            self.pulse_freq = val
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


