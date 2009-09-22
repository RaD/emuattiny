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
    """ This procedure check record count+addrH+addrL+type+sum(dd)+ss ==
    0x00.  If checksum doesn't match, it raises exceptions, else
    silently return. """
    checking = reduce(lambda x,y: x + y, [int(record[i*2:i*2+2], 16) for i in [x for x in xrange(len(record)/2)]])
    if ('%02x' % checking)[-2:] != '00':
        raise Exception ('ERROR: Checksum doesn\' match! Record is %s' % (record, ))

def int2bin(n, count=16):
    return "".join([str((n >> y) & 1) for y in range(count-1, -1, -1)])

def set_bit(x, bitnum):
    return x | 1 << bitnum

def clear_bit(x, bitnum):
    return x & ~(1 << bitnum)

def check_bit(x, bitnum):
    return (x & (1 << bitnum)) != 0

def get_port_by_name(port_list, name):
    return filter(lambda x: port_list[x] == name.upper(), port_list)[0]

def get_port_value(port_list, number):
    return port_list[number]

def set_flag(port_list, flag, action='reset'):
    port_number = get_port_by_name('sreg')
    port_list[port_number] = set_bit(

def reset_C_flag():
    pass

def parse_opcode(addr, word):
    """ This function return appropriate assembler mnemonic. """
    from attiny13 import mnemonics, logics
    b = int2bin(int(word, 16))
    for mnemo, regexp, mtype in mnemonics:
        m = re.match(regexp, b)
        if m:
            (fields, func) = logics.get(mtype, (tuple(), lambda addr: None))

            args = [addr]
            for k in fields:
                args.append(m.group(k))

            if callable(func):
                #print b, mnemo, func(*args)
                return (mnemo, func(*args))
            else:
                #print b, mnemo
                return (mnemo, ())
    
def build_code_tree(filename):
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
            #print '%s: %s' % (record_types[rtype], data)
            segment_address = int(data, 16)
        elif rtype == '01':
            #print '%s' % (record_types[rtype], )
            pass
        elif rtype == '00':
            record_start_address = segment_address + int(addr, 16)
            op_addr = record_start_address
            for i in xrange(len(data)/4):
                word = '%s%s' % (data[i*4+2:i*4+4], data[i*4:i*4+2])
                (mnemo, value) = parse_opcode(op_addr, word)
                #print record_start_address, op_addr, mnemo, value
                if type(value) is tuple:
                    if mnemo == 'eor' and value[0] == value[1]:
                        mnemo = 'clr'
                        value = value[0]
                code_tree.update({'%04x' % op_addr: (mnemo, value)})
                op_addr += 2
        else:
            continue
    return code_tree

def show_registers():
    for i in xrange(8):
        for j in xrange(4):
            val = registers['r%02i' % (j * 8 + i)]
            print 'r%02i = % 4i : 0x%02x : %s\t' % (j * 8 + i, val, val, int2bin(val, 8)),
        print
    print

def show_ports():
    for i in ports_name.keys():
        key = ports_name[i]
        val = ports_values[i]
        print '%02x : %s\t= % 4i : 0x%02x : %s' % (int(i, 16), key, val, val, int2bin(val, 8))
    print

def show_scope(pointer):
    list = pointer - 8
    if list < 0:
        list = 0
    for i in xrange(8):
        mnemo = code_tree.get('%04x' % (list + i * 2), None)
        if not mnemo:
            pass
        (command, args) = mnemo
        if args:
            print '%04x : %s \t %s' % (list + i * 2, command, args)
        else:
            print '%04x : %s' % (list + i * 2, command)
    print

def show_stack():
    for i in stack:
        print '[ %i ]' % i
    print

def process_opcode(pointer):
    if command == 'cli':
        ports_values['3f'] = clear_bit(ports_values['3f'], 7) # I
    if command == 'clr':
        ports_values['3f'] = ports_values['3f'] | 1 << 1 | 0 << 2 | 0 << 3 | 0 << 4 # Z N V S
        registers[args] = 0
    if command == 'in':
        key = args[1].split('x')[1]
        value = ports_values[key]
        registers[args[0]] = value
    if command == 'ldi':
        registers[args[0]] = int(args[1], 2)
    if command == 'ori':
        value = registers[args[0]] | int(args[1], 2)
        ports_values['3f'] = ports_values['3f'] \
            | 0 << 3 \
            | (value == 0 and 1 or 0) << 1 \
            | (check_bit(value, 7) and 1 or 0) << 2
        registers[args[0]] = value
    if command == 'out':
        value = registers[args[1]]
        key = args[0].split('x')[1]
        ports_values[key] = value
    if command == 'pop':
        registers[args] = stack.pop()
    if command == 'push':
        stack.append(registers[args])
    if command == 'rcall':
        stack.append(pointer)
        pointer = int(args, 16) - 2
    if command == 'ret':
        pointer = stack.pop()
    if command == 'reti':
        ports_values['3f'] = set_bit(ports_values['3f'], 7)
        pointer = stack.pop() - 2
    if command == 'rjmp':
        pointer = int(args.split('x')[1], 16) - 2
    if command == 'sbic':
        if not check_bit(registers[args[0]], args[1]):
            pointer += 2;
    if command == 'sbrs':
        if check_bit(registers[args[0]], args[1]):
            pointer += 2;
    if command == 'sei':
        ports_values['3f'] = set_bit(ports_values['3f'], 7)
    pointer += 2
    return pointer

if __name__ == '__main__':
    from attiny13 import ports as ports_name
    copyright()

    pointer = 0
    registers = {}
    ports_values = {}
    stack = []

    code_tree = build_code_tree(options.hexfile)

    [registers.update({'r%02i' % r: 0}) for r in xrange(32)]
    [ports_values.update({p: 0}) for p in ports_name.keys()]

    show_scope(pointer)
    while True:
        addr = '%04x' % pointer
        mnemo = code_tree.get(addr, None)
        if not mnemo:
            raise Exception('ERROR: %04x' % pointer)
        (command, args) = mnemo

        if args:
            print addr, ': ', command, '\t', args
        else:
            print addr, ': ', command
        
        user = raw_input('# ')

        if user in ['q', 'quit']:
            break
        if user in ['h', 'help']:
            help_info()
        if user in ['r', 'regs']:
            show_registers()
        if user in ['p', 'ports']:
            show_ports()
        if user in ['l', 'list']:
            show_scope(pointer)
        if user in ['s', 'stack']:
            show_stack()
        if user in ['t', 'int timer']: # timer interrupt
            sreg_port = get_port_by_name(ports_name, 'sreg')
            sreg_value = get_port_value(ports_values, sreg_port)
            if check_bit(sreg_value, 7):
                stack.append(pointer)
                pointer = 6
                print 'timer interrupt'
            else:
                print 'interrupts are not allowed'
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
                    print 'matched', dest, pres
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
            pointer = process_opcode(pointer)

    sys.exit(0)
