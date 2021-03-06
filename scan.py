#!/usr/bin/env python3.4
"""tools for scan TCP ports"""
import socket
import threading
import sys
# import time
import getopt


_mutex = threading.Lock()
HELP_LEVEL = """
    0 - without message
    1 - only close port(timeout)
    2 - block port
    3 - only open port
    4 - show all"""
LOG_LEVEL = '3'
PRINT_NAME = False
HOSTS_ADDR_NAME = dict()


def using():
    """hepl for using and EXIT"""
    print("""
-h --help \t for help
-l --log \t for set log level
%s
-t --thread --threads \t for set number threads

EXAMPLE
./scan.py -t 10 -l 4 127.0.0.1 127.0.1.1 20 30
    """ % HELP_LEVEL)
    sys.exit(0)


def send_msg(msg='', host='', port='', lvl='0'):
    """message on screen"""
    if LOG_LEVEL == '4' or not LOG_LEVEL.find(lvl) < 0:
        if PRINT_NAME and not host == '' and not HOSTS_ADDR_NAME[host] == '':
            name = HOSTS_ADDR_NAME[host]
            print('%s %s:%s %s' % (name, host, port, msg))
        elif not host == '':
            print('%s:%s %s' % (host, port, msg))
        else:
            print('%s' % (msg,))


def check_host(host):
    """check correct ip address"""
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
    """generate next host"""
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
    """get yield next port"""
    global HOSTS_ADDR_NAME
    while True:
        try:
            if PRINT_NAME:
                try:
                    HOSTS_ADDR_NAME[host1] = socket.gethostbyaddr(host1)[0]
                except ValueError:
                    # print('ValueError')
                    HOSTS_ADDR_NAME[host1] = ''
                except OSError:
                    # print('OSError')
                    HOSTS_ADDR_NAME[host1] = ''
            else:
                HOSTS_ADDR_NAME[host1] = ''
            host1 = next_host(host1, host2)
        except OSError:
            # print('EXCEPT2')
            break
    # print('HOSTS_ADDR_NAME: ', HOSTS_ADDR_NAME)
    for host in HOSTS_ADDR_NAME:
        for port in range(port1, port2 + 1):
            yield {'host': host, 'port': port}


def check_params(input_line):
    """check enter input parameters"""
    param1 = 't:l:hn'
    param2 = ['thread=', 'threads=', 'log=', 'help', 'name']
    opts, args = None, None
    try:
        opts, args = getopt.getopt(input_line[1:], param1, param2)
    except getopt.GetoptError:
        using()
    host1 = None
    host2 = None
    port1 = None
    port2 = None
    num_ths = 1
    print('opts:', opts)
    print('args:', args)
    for arg, opt in opts:
        if arg in '-h,--help'.split(','):
            using()
        if arg in '-n,--name'.split(','):
            global PRINT_NAME
            PRINT_NAME = True
        if arg in '-l,--log'.split(','):
            tmp_lvl = int(opt)
            if not 0 > tmp_lvl:
                global LOG_LEVEL
                LOG_LEVEL = opt
        if arg in '-t,--thread,--threads'.split(','):
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
    """check connect to TCP port on host"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.connect((host, port))
        send_msg(msg='connected ', host=host, port=str(port), lvl='3')
    # except ConnectionRefusedError:
    except socket.timeout:
        send_msg(msg='timeout ', host=host, port=str(port), lvl='1')
    except socket.error as err:
        msg = err.__str__()
        send_msg(msg=msg, host=host, port=str(port), lvl='2')
#    except OSError:
#        print('OSError', host, port)


def pth(getter, name):
    """thread for get link host-port"""
    quan = 0
    while True:
        try:
            with _mutex:
                host_port = getter.__next__()
            # print(name, host_port['host'], host_port['port'])
            scan(host_port['host'], host_port['port'])
            quan += 1
        except StopIteration:
            break
    send_msg(msg=name + ' ' + str(quan), lvl='4')


def main():
    """main func for running"""
    num_threads, host1, host2, port1, port2 = check_params(sys.argv)
    if not host2:
        host2 = host1
    if not port2:
        port2 = port1
    if not host1 or not len(host1.split('.')) == 4 or not port1:
        using()

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
    # pth(getter)


if __name__ == '__main__':
    main()
