#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) 2009 Ruslan Popov <ruslan.popov@gmail.com>

import sys, re
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
    from hex_loader import HexLoader

    alu = ATtiny13()
    loader = HexLoader(alu, options.hexfile)

    code_tree = loader.get_code_tree()

    show_scope(alu.get_pointer())
    while True:
        addr = '%04x' % alu.get_pointer()
        mnemo = code_tree.get(addr, None)
        if not mnemo:
            raise Exception('ERROR: %04x' % alu.get_pointer())
        (command, args) = mnemo

        alu.show(command, args)

        user = raw_input('# ')

        if user in ['n', 'next']:
            alu.process(command, args)
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
                        port_addr = alu.get_port_by_name(port_name)
                        alu.set_port(ports_values[port_addr], value)
                    else:
                        reg_name = 'r%s' % m.group('reg_number')
                        alu.set_reg(reg_name, value)
                    break

    sys.exit(0)
