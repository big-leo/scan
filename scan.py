#!/usr/bin/env python3.4
'''tools for scan TCP ports'''
import socket
import threading
import sys
import time
import getopt

_mutex = threading.Lock()


def check_host(host):
    '''check correct ip address'''
    elements = host.split('.')
    if len(elements) != 4:
        raise OSError
    for element in elements:
        try:
            int(element)
        except ValueError:
            raise OSError


def bigger_ip(host1, host2):
    """ return True if host1 > host2"""
    list1 = host1.split('.')
    list2 = host2.split('.')
    for i in range(4):
        if int(list1[i]) > int(list2[i]):
            return True
        elif int(list1[i]) < int(list2[i]):
            return False
    return False


def next_host(host_before, host_last):
    '''generate next host'''
    if host_before == host_last:
        raise OSError
    elements = host_before.split('.')
    if len(elements) != 4:
        raise OSError
    if int(elements[3]) < 254:
        elements[3] = str(int(elements[3]) + 1)
    else:
        elements[3] = '1'
        if int(elements[2]) < 254:
            elements[2] = str(int(elements[2]) + 1)
        else:
            elements[2] = '0'
            if int(elements[1]) < 254:
                elements[1] = str(int(elements[1]) + 1)
            else:
                elements[1] = '0'
                if int(elements[0]) < 254:
                    elements[0] = str(int(elements[0]) + 1)
                else:
                    raise OSError
    return '.'.join(elements)


def next_host_port(host1, host2, port1, port2):
    '''get yield next port'''
    array_host = []
    while True:
        try:
            array_host.append(host1)
            host1 = next_host(host1, host2)
        except OSError:
            break
    #print('array_host: ', array_host)
    for host in array_host:
        for port in range(port1, port2 + 1):
            yield {'host': host, 'port': port}


def check_params(input_line):
    '''check enter input parameters'''
    opts, args = getopt.getopt(input_line[1:], 't:')
    host1 = None
    host2 = None
    port1 = None
    port2 = None
    num_ths = 1
    print('opts:', opts)
    print('args:', args)
    for arg, opt in opts:
        if arg == '-t':
            try:
                num_ths = int(opt)
                if not num_ths > 0:
                    num_ths = 1
            except ValueError:
                print('fool quan threads')
    for arg in args:
        try:
            if port1:
                port2 = int(arg)
            else:
                port1 = int(arg)
        except ValueError:
            print(arg, 'Not port')
            try:
                check_host(arg)
                if host1:
                    host2 = arg
                else:
                    host1 = arg
            except OSError:
                print(arg, 'Not host')
    return num_ths, host1, host2, port1, port2


def scan(host, port):
    '''check connect to TCP port on host'''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.connect((host, port))
        print('connected:', host, ':', port)
    except ConnectionRefusedError:
        print('Blocking Connection Refused Error %s %s' % (host, port))
    except socket.timeout:
        print('timeout', host, port)
#    except OSError:
#        print('OSError', host, port)


def pth(getter, name):
    '''thread for get link host-port'''
    quan = 0
    while True:
        try:
            with _mutex:
                host_port = getter.__next__()
            #print(name, host_port['host'], host_port['port'])
            scan(host_port['host'], host_port['port'])
            quan += 1
        except StopIteration:
            break
    print(name, str(quan))

def main():
    '''main func for running'''
    num_threads, host1, host2, port1, port2 = check_params(sys.argv)
    if not host2:
        host2 = host1
    if not port2:
        port2 = port1
    if bigger_ip(host1, host2):
        temp = host1
        host1 = host2
        host2 = temp
    if port2 < port1:
        temp = port1
        port1 = port2
        port2 = temp
    print('threads:', num_threads)
    print('host1:', host1)
    print('host2:', host2)
    print('port1:', port1)
    print('port2:', port2)

    getter = next_host_port(host1, host2, port1, port2)
    threads = []
    for num in range(num_threads):
        th_name = 'th' + str(num)
        thread = threading.Thread(name=th_name, target=pth, args=(getter, th_name))
        threads.append(thread)

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    #pth(getter)


if __name__ == '__main__':
    main()
