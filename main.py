import re
import socket
import time

UDP_IP = '192.168.1.121'
UDP_IN_PORT = 55556
UDP_OUT_PORT = 55555

in_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
out_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
in_sock.bind((UDP_IP, UDP_IN_PORT))

faults = True  # Set this to True to indicate generator fault(s)


def StripMsg(bdata):
    sdata = bdata.decode('UTF-8')
    pat = re.compile('\$[a-z](.+?)#')  # Match all characters between $? and #
    m = pat.match(sdata)
    # return m.group(0)[1], m.group(1).split(' ')
    return m.group(0)[1], m.group(1)


def SendMsg(message, addr, seq):
    chk = GenerateChecksum(seq + ' ' + message)
    respstr = f'{seq} {message}#{chk[2:].zfill(2)}\r'
    # respstr = f'{seq}{message}#{chk}\r\x00'
    respbytes = respstr.encode('utf-8')  # Convert string to byte object
    # print(f'Sending {respbytes} to {addr}')
    out_sock.sendto(respbytes, (addr, UDP_OUT_PORT))


def GenerateChecksum(message):
    s = 0
    for i in range(len(message)):
        s += ord(message[i])
    return hex(~s & 0xff).upper()  # Mask to one byte, invert and return


while True:
    data, addr = in_sock.recvfrom(1024)  # buffer size is 1024 bytes - BLOCKS
    seq, msg = StripMsg(data)
    # print(f'{addr[0]} sent msg: {data} extracted to: {msg} with seq: {seq}')
    # print(f'Received : {seq} : {msg}')
    # print(f'msg checksum = {GenerateChecksum(seq+msg)}')
    time.sleep(0.05)  # Delay response from command just a bit
    if msg == 'U TMFP':
        resp = '1'
        SendMsg(resp, addr[0], seq)
    elif msg == 'SUT 0':
        resp = '0'
        SendMsg(resp, addr[0], seq)
    elif msg == 'RCAT':
        resp = 'TUBE239DT'
        SendMsg(resp, addr[0], seq)
    elif msg == 'SBV 60.0':
        resp = '0'
        SendMsg(resp, addr[0], seq)
    elif msg == 'RPF':
        resp = '50000.000'
        SendMsg(resp, addr[0], seq)
    elif msg == 'RPD':
        resp = '20.000'
        SendMsg(resp, addr[0], seq)
    elif msg == 'RP1D':
        resp = '0.000'
        SendMsg(resp, addr[0], seq)
    elif msg == 'RP1W':
        resp = '45.000'
        SendMsg(resp, addr[0], seq)
    elif msg == 'MP':
        if faults:
            resp = '32'
        else:
            resp = '256'
        SendMsg(resp, addr[0], seq)
    elif msg == 'MAV MBC MRC':
        resp = '0.000 0.000 0.000'
        SendMsg(resp, addr[0], seq)
    elif msg == 'MFA MF1' or msg == 'MFA MF2' or msg == 'MFA MF3' or \
            msg == 'MFA MF4' or msg == 'MFA MF5' or msg == 'MFA MF6':
        if faults:
            resp = '0x0002 0x0000 0x0000 0x0000 0x0400 0x0020 2'
        else:
            resp = '0x0000 0x0000 0x0000 0x0000 0x0000 0x0000 0'
        SendMsg(resp, addr[0], seq)
    elif msg == 'MFG':
        if faults:
            resp = '1'
        else:
            resp = '0'
        SendMsg(resp, addr[0], seq)
    elif msg == 'MH MAH':
        resp = '1250367 71878544'
        SendMsg(resp, addr[0], seq)
    elif msg == 'MTC MTT MTP MEI':
        resp = '36.239 21.990 120.003 27.0'
        SendMsg(resp, addr[0], seq)
    elif msg == 'C':  # (C)lear faults
        resp = '0'
        SendMsg(resp, addr[0], seq)
        faults = False
    elif msg == 'Q':  # (Q)uit  [emergency shutdown]
        resp = '0'
        SendMsg(resp, addr[0], seq)
        faults = True
    else:
        print(f'Unexpected message : {msg}')
