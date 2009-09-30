#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) 2009 Ruslan Popov <ruslan.popov@gmail.com>

import os, sys, re
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-f", "--hex-file", action="store", dest="hexfile",
                  help="HEX file", default=None)
(options, args) = parser.parse_args()

for key in ['hexfile']:
    if not getattr(options, key, None):
        print 'ERROR: Parameter %s is required!' % (key, )
        parser.print_help()
        sys.exit(1)

record_types = {'00': 'Data', 
                '01': 'End of File', 
                '02': 'Extended Segment Address',
                '03': 'Start Segment Address', 
                '04': 'Extended Linear Address',
                '05': 'Start Linear Address'}

def copyright():
    print '\n(c)2009 Ruslan Popov - The simplest ATtiny13\'s emulator.\n'

def help_info():
    copyright()
    print 'Usage'
    print '\tr[egs]      - show registers'
    print '\tp[orts]     - show ports'
    print '\tl[ist]      - show scope'
    print '\ts[stack]    - show stack'
    print '\tn[ext]      - execute line'
    print
    print '\tt|int timer - raise timer interrupt'
    print 
    print '\tset r<regnum>=[0b|0x]<value> - set register\'s value'
    print '\tset p<name>=[0b|0x]<value>   - set port\'s value'
    print '\texamples:'
    print '\t\tset r16=0b01010101 \tset r17=0x2a \t\tset r18=99'
    print '\t\tset psreg=0b01010101 \tset pportb=0x2a \tset ppinb=99'
    print

def check_record(record):
    """ Checks record count+addrH+addrL+type+sum(dd)+ss == 0x00. If
    checksum doesn't match, it raises exceptions, else silently
    return. """
    checking = reduce(lambda x,y: x + y, [int(record[i*2:i*2+2], 16) for i in [x for x in xrange(len(record)/2)]])
    if ('%02x' % checking)[-2:] != '00':
        raise Exception ('ERROR: Checksum doesn\' match! Record is %s' % (record, ))


def set_bit(x, bitnum):
    """ Sets appropriate bit. """
    return x | 1 << bitnum

def clear_bit(x, bitnum):
    """ Clears appropriate bit. """
    return x & ~(1 << bitnum)

def check_bit(x, bitnum):
    """ Checks if appropriate bit is set. """
    return (x & (1 << bitnum)) != 0

def get_port_by_name(port_list, name):
    """ Get port's number by its name. """
    return filter(lambda x: port_list[x] == name.upper(), port_list)[0]

def get_port_value(port_list, number):
    """ Get the value of appropriate port. """
    return port_list[number]

def set_flag(port_list, flags, action='reset'):
    """ Set the SREG bits. """
    flags = {'i': 7, 't': 6, 'h': 5, 's': 4, 'v': 3, 'n': 2, 'z': 1, 'c': 0}
    port_number = get_port_by_name(port_list, 'sreg')
    try:
        value = port_list[port_number]
        bitnum = flags[flag]
    except:
        raise Exception('ERROR: Wrong flag!')
    action_func = None
    if action == 'set':
        action_func = set_bit
    else:
        action_func = clear_bit
    if type(flags) is tuple:
        for i in flags:
            port_list[port_number] = action_func(value, bitnum)
    else:
        port_list[port_number] = action_func(value, bitnum)

def build_code_tree(alu, filename):
    """ Builds code tree. """
    if not os.path.isfile(filename):
        raise Exception('ERROR: Does the %s exist?' % (filename, ))
    hex = open(filename, 'r').read().split('\r\n')

    code_tree = {}
    segment_address = 0

    for line in hex:
        if len(line) == 0:
            continue
        check_record(line[1:])
        regexp = re.compile(r"""
                 ^\: # intel hex record start byte
                  (?P<count>[0-9A-F]{2}) # record's byte count
                  (?P<addr>[0-9A-F]{4}) # record's first address
                  (?P<type>[0-9A-F]{2}) # record type
                  (?P<data>[0-9A-F]*) # actual data (0..255 bytes)
                  (?P<checksum>[0-9A-F]{2}) # checksum
                 $""", re.X)
        m = re.match(regexp, line)
        if not m:
            raise Exception('ERROR: This is not Intel HEX!')
        (count, addr, rtype, data, checksum) = m.group('count', 'addr', 'type', 'data', 'checksum')

        if rtype == '02':
            segment_address = int(data, 16)
        elif rtype == '01':
            pass
        elif rtype == '00':
            record_start_address = segment_address + int(addr, 16)
            op_addr = record_start_address
            for i in xrange(len(data)/4):
                word = '%s%s' % (data[i*4+2:i*4+4], data[i*4:i*4+2])
                (mnemo, value) = alu.parse(op_addr, word)

                # operand synonyms
                if type(value) is tuple:
                    if mnemo == 'eor' and value[0] == value[1]:
                        mnemo = 'clr'
                        value = value[0]

                code_tree.update({'%04x' % op_addr: (mnemo, value)})
                op_addr += 2
        else:
            continue
    return code_tree

def show_registers(alu):
    """ Shows current state of registers. """
    registers = alu.get_regs()
    for i in xrange(8):
        for j in xrange(4):
            val, binval = registers['r%02i' % (j * 8 + i)]
            print 'r%02i = % 4i : 0x%02x : %s\t' % (j * 8 + i, val, val, binval),
        print
    print

def show_ports(alu):
    """ Shows current state of I/O ports. """
    for i, key, val, binval in alu.get_ports():
        print '%02x : %s\t= % 4i : 0x%02x : %s' % (int(i, 16), key, val, val, binval)
    print

def show_scope(pointer):
    """ Shows current scope. """
    list = pointer - 16
    if list < 0:
        list = 0
    for i in xrange(16):
        (command, args) = code_tree.get('%04x' % (list + i * 2), (None, None))
        if args:
            print '%04x : %s \t %s' % (list + i * 2, command, args)
        else:
            print '%04x : %s' % (list + i * 2, command)
    print

def show_stack(alu):
    """ Shows current state of the stack. """
    for i in alu.get_stack():
        print '[ %i ]' % i
    print

if __name__ == '__main__':
    copyright()

    from attiny13 import ATtiny13
    alu = ATtiny13()

    code_tree = build_code_tree(alu, options.hexfile)

    show_scope(alu.get_pointer())
    while True:
        addr = '%04x' % alu.get_pointer()
        mnemo = code_tree.get(addr, None)
        if not mnemo:
            raise Exception('ERROR: %04x' % pointer)
        (command, args) = mnemo
        
        alu.show(command, args)

        user = raw_input('# ')

        if user in ['q', 'quit']:
            break
        if user in ['h', 'help']:
            help_info()
        if user in ['r', 'regs']:
            show_registers(alu)
        if user in ['p', 'ports']:
            show_ports(alu)
        if user in ['s', 'stack']:
            show_stack(alu)
        if user in ['l', 'list']:
            show_scope(alu.get_pointer())
        if user in ['t', 'int timer']: # timer interrupt
            alu.init_exception('tim0_ovf')
        if user.startswith('set'):
            set_re = [
                ('port', 'binary', '^set p(?P<port_name>[A-Za-z0-9]+)=0b(?P<value>[01]+)'),
                ('port', 'hex', '^set p(?P<port_name>[A-Za-z0-9]+)=0x(?P<value>[A-Fa-f0-9]+)'),
                ('port', 'decimal', '^set p(?P<port_name>[A-Za-z0-9]+)=(?P<value>[0-9]+)'),
                ('register', 'binary', '^set r(?P<reg_number>[A-Za-z0-9]+)=0b(?P<value>[01]+)'),
                ('register', 'hex', '^set r(?P<reg_number>[A-Za-z0-9]+)=0x(?P<value>[A-Fa-f0-9]+)'),
                ('register', 'decimal', '^set r(?P<reg_number>[A-Za-z0-9]+)=(?P<value>[0-9]+)'),
                ]
            for dest, pres, regexp in set_re:
                m = re.match(regexp, user)
                if m:
                    #print 'matched', dest, pres
                    if pres == 'binary':
                        value = int(m.group('value'), 2)
                    elif pres == 'hex':
                        value = int(m.group('value'), 16)
                    else:
                        value = int(m.group('value'))
                    if dest == 'port':
                        port_name = m.group('port_name')
                        port_addr = get_port_by_name(port_name)
                        ports_values[port_addr] = value
                    else:
                        reg_name = 'r%s' % m.group('reg_number')
                        registers[reg_name] = value
                    break
        if user in ['n', 'next']:
            alu.process(command, args)

    sys.exit(0)
