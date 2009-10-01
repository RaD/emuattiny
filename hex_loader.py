# -*- coding: utf-8 -*-
# (c) 2009 Ruslan Popov <ruslan.popov@gmail.com>

import os, re

class HexLoader(object):

    def __init__(self, alu, filename, *args, **kwargs):
        self.alu = alu
        self.filename = filename
        self.record_types = {'00': 'Data',
                             '01': 'End of File',
                             '02': 'Extended Segment Address',
                             '03': 'Start Segment Address',
                             '04': 'Extended Linear Address',
                             '05': 'Start Linear Address'}

    def check_record(self, record):
        """ Checks record count+addrH+addrL+type+sum(dd)+ss == 0x00. If
        checksum doesn't match, it raises exceptions, else silently
        return. """
        checking = reduce(lambda x,y: x + y, [int(record[i*2:i*2+2], 16) for i in [x for x in xrange(len(record)/2)]])
        if ('%02x' % checking)[-2:] != '00':
            raise Exception ('ERROR: Checksum doesn\' match! Record is %s' % (record, ))

    def get_code_tree(self):
        """ Builds code tree. """
        if not os.path.isfile(self.filename):
            raise Exception('ERROR: Does the %s exist?' % (self.filename, ))
        hex = open(self.filename, 'r').read().split('\r\n')

        code_tree = {}
        segment_address = 0

        for line in hex:
            if len(line) == 0:
                continue
            self.check_record(line[1:])
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
                    (mnemo, value) = self.alu.parse(op_addr, word)

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

