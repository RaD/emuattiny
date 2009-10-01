# -*- coding: utf-8 -*-
# (c) 2009 Ruslan Popov <ruslan.popov@gmail.com>

import operator, re
from alu import ALU

class ATtiny13(ALU):

    def __init__(self, *args, **kwargs):
        super(ATtiny13, self).__init__(*args, **kwargs)

        self.port_names = {'03': 'ADCSRB', '04': 'ADCL', '05': 'ADCH',  '06': 'ADCSRA',
                      '07': 'ADMUX',  '08': 'ACSR', '14': 'DIDR0', '15': 'PCMSK',
                      '16': 'PINB',   '17': 'DDRB', '18': 'PORTB', '1C': 'EECR',
                      '1D': 'EEDR',
                      '26': 'CLKPR', '28': 'GRCCR',
                      '32': 'TCNT0', '39': 'TIMSK0',
                      '3d': 'SPL',
                      '3f': 'SREG' }

        [self.reg_vals.update({'r%02i' % r: 0}) for r in xrange(32)]
        [self.port_vals.update({p: 0}) for p in self.port_names.keys()]

        self.mnemonics = {
            'adc': ('^000111(?P<ra>[01]{1})(?P<rd>[01]{5})(?P<rb>[01]{4})$', 'rd_rr', self.adc),
            'add': ('^000011(?P<ra>[01]{1})(?P<rd>[01]{5})(?P<rb>[01]{4})$', 'rd_rr', self.add),
            'and': ('^001000(?P<ra>[01]{1})(?P<rd>[01]{5})(?P<rb>[01]{4})$', 'rd_rr', lambda: 'and'),
            'andi': ('^0111(?P<ka>[01]{4})(?P<rd>[01]{4})(?P<kb>[01]{4})$', 'rd_k', self.andi),
            'bld': ('^1111100(?P<rd>[01]{5})0(?P<b>[01]{3})$', 'rd_b', self.bld),
            'brcc': ('^111101(?P<k>[01]{7})000$', 'k', self.brcc),
            'brcs': ('^111100(?P<k>[01]{7})000$', 'k', lambda: 'brcs'),
            'breq': ('^111100(?P<k>[01]{7})001$', 'k', lambda: 'breq'),
            'brne': ('^111101(?P<k>[01]{7})001$', 'k', self.brne),
            'bst': ('^1111101(?P<rd>[01]{5})0(?P<b>[01]{3})$', 'rd_b', self.bst),
            'cbi': ('^10011000(?P<a>[01]{5})(?P<b>[01]{3})$', 'a_b', self.cbi),
            'cli': ('^(?P<op>1001010011111000)$', None, self.cli),
            'clr': (None, None, self.clr),
            'com': ('^1001010(?P<rd>[01]{5})0000$', 'rd', lambda: 'com'),
            'cpi': ('^0011(?P<ka>[01]{4})(?P<rd>[01]{4})(?P<kb>[01]{4})$', 'rd_k', lambda: 'cpi'),
            'dec': ('^1001010(?P<rd>[01]{5})1010$', 'rd', self.dec),
            'eor': ('^001001(?P<ra>[01]{1})(?P<rd>[01]{5})(?P<rb>[01]{4})$', 'rd_rr', lambda: 'eor'),
            'in': ('^10110(?P<aa>[01]{2})(?P<rd>[01]{5})(?P<ab>[01]{4})$', 'rd_a', self.in_op),
            'ldi': ('^1110(?P<ka>[01]{4})(?P<rd>[01]{4})(?P<kb>[01]{4})$', 'rd_k', self.ldi),
            'mov': ('^001011(?P<ra>[01]{1})(?P<rd>[01]{5})(?P<rb>[01]{4})$', 'rd_rr', self.mov),
            'or': ('^001010(?P<ra>[01]{1})(?P<rd>[01]{5})(?P<rb>[01]{4})$', 'rd_rr', self.or_op),
            'ori': ('^0110(?P<ka>[01]{4})(?P<rd>[01]{4})(?P<kb>[01]{4})$', 'rd_k', self.ori),
            'out': ('^10111(?P<aa>[01]{2})(?P<rr>[01]{5})(?P<ab>[01]{4})$', 'a_rr', self.out),
            'pop': ('^1001000(?P<rd>[01]{5})1111$', 'rd', self.pop),
            'push': ('^1001001(?P<rd>[01]{5})1111$', 'rd', self.push),
            'rcall': ('^1101(?P<k>[01]{12})$', 'k', self.rcall),
            'ret': ('^(?P<op>1001010100001000)$', None, self.ret),
            'reti': ('^(?P<op>1001010100011000)$', None, self.reti),
            'rjmp': ('^1100(?P<k>[01]{12})$', 'k', self.rjmp),
            'rol': ('^000111(?P<ra>[01]{1})(?P<rd>[01]{5})(?P<rb>[01]{4})$', 'rd_rr', self.rol),
            'ror': ('^1001010(?P<rd>[01]{5})0111$', 'rd', self.ror),
            'sbi': ('^10011010(?P<a>[01]{5})(?P<b>[01]{3})$', 'a_b', lambda: 'sbi'),
            'sbic': ('^10011001(?P<a>[01]{5})(?P<b>[01]{3})$', 'a_b', self.sbic),
            'sbrc': ('^1111110(?P<rr>[01]{5})0(?P<b>[01]{3})', 'rr_b', lambda: 'sbrc'),
            'sbrs': ('^1111111(?P<rr>[01]{5})0(?P<b>[01]{3})', 'rr_b', self.sbrs),
            'sei': ('^(?P<op>1001010001111000)$', None, self.sei),
            }

        self.logics = {
            'a_b': (('a', 'b'),
                    lambda addr, a, b: (int(a,2), int(b,2))),
            'a_rr': (('aa', 'ab', 'rr'),
                     lambda addr, aa, ab, rr: (int('%s%s' % (aa, ab), 2),
                                               'r%s' % int(rr,2))),
            'k': (('k',),
                  lambda addr, k: (int(k, 2), k.startswith('1'))),
            'rd': (('rd',),
                   lambda addr, rd: 'r%s' % int(rd,2)),
            'rd_a': (('aa', 'ab', 'rd'),
                     lambda addr, ka, kb, rd: ('r%i' % (int(rd,2)),
                                               int('%s%s' % (ka, kb),2))),
            'rd_b': (('rd', 'b'),
                     lambda addr, rd, b: ('r%s' % int(rd,2), int(b,2))),
            'rd_k': (('ka', 'kb', 'rd'),
                     lambda addr, ka, kb, rd: ('r%s' % (int(rd,2) + 16),
                                               int('%s%s' % (ka, kb), 2))),
            'rd_rr': (('ra', 'rb', 'rd'),
                      lambda addr, ra, rb, rd: ('r%s' % int(rd,2),
                                                'r%s' % int('%s%s' % (ra, rb),2))),
            'rr_b': (('rr', 'b'),
                     lambda addr, rr, b: ('r%i' % (int(rr,2)), int(b,2)))
            }

    def get_pointer(self):
        return self.pointer

    def get_regs(self):
        result = {}
        for key in self.reg_vals.keys():
            val = self.reg_vals[key]
            result.update({key: (val, self.int2bin(val, 8))})
        return result

    def get_ports(self):
        result = []
        for i in self.port_names.keys():
            key = self.port_names[i]
            val = self.port_vals[i]
            result.append((i, key, val, self.int2bin(val, 8)))
        return result

    def get_port_by_name(self, port_name):
        for id, name in self.port_names.items():
            if name == port_name:
                return id
        return None

    def get_stack(self):
        return self.stack

    def init_exception(self, name):
        exceptions = {'tim0_ovf': 6,
                      }
        value = self.port_vals['3f']
        if self.check_bit(value, 7):
            self.stack.append(self.pointer)
            self.pointer = exceptions[name]
            print '%s interrupt' % (name, )
        else:
            print 'interrupts are not allowed'

    def parse(self, addr, word):
        """ Returns appropriate assembler mnemonic. """
        b = self.int2bin(int(word, 16))

        for mnemo in self.mnemonics.keys():
            (regexp, mtype, func) = self.mnemonics[mnemo]
            if regexp is None:
                continue
            m = re.match(regexp, b)
            if m:
                (fields, func) = self.logics.get(mtype, (tuple(), lambda addr: None))

                args = [addr]
                for k in fields:
                    args.append(m.group(k))

                if callable(func):
                    return (mnemo, func(*args))
                else:
                    return (mnemo, ())

    def show(self, command, args):
        (regexp, mtype, func) = self.mnemonics[command]
        func(args, True)

    def process(self, command, args):
        (regexp, mtype, func) = self.mnemonics[command]
        func(args, False)

    def common_logic(self, command, action, args, print_line):
        (rd, k) = args
        value = action(self.reg_vals[rd], k)
        if not print_line:
            # s = n xor v
            self.sreg_clear('v')
            # n = r7
            # z = neg(r7) and neg(r6) and .. and neg(r0)
            self.reg_vals[rd] = value
            self.pointer += 2
        else:
            print '%04x : %s\t%s, 0b%s' % (self.pointer, command, rd, self.int2bin(k, 8))

    def common_checkio(self, command, args, print_line):
        (a, b) = args
        a_hex = '%02x' % a
        if not print_line:
            if not self.check_bit(self.port_vals[a_hex], b):
                self.pointer += 2;
            self.pointer += 2
        else:
            print '%04x : %s\t$%02x, %s' % (self.pointer, command, a, b)

    def common_branch(self, command, range, args, print_line):
        (k, is_negative) = args
        if is_negative:
            k -= range
        if not print_line:
            if command == 'brne' and self.sreg_check('z'):
                self.pointer += 2 * k + 2
            #self.pointer += 2
        else:
            print '%04x : %s\t%04x' % (self.pointer, command, self.pointer + 2 * k + 2),
            print '\t\t[i:%s][t:%s][h:%s][s:%s][v:%s][n:%s][z:%s][c:%s]' % tuple([z for z in self.int2bin(self.get_sreg(), 8)])

    def adc(self, args, print_line):
        (rd, rr) = args
        if not print_line:
            self.reg_vals[rd] += self.reg_vals[rr]
            if self.check_bit(self.port_vals['3f'], 0):
                self.reg_vals[rd] += 1
            # SET FLAGS HERE
            self.pointer += 2
        else:
            print '%04x : adc\t%s, %s' % (self.pointer, rd, rr)

    def add(self, args, print_line):
        (rd, rr) = args
        if not print_line:
            self.reg_vals[rd] += self.reg_vals[rr]
            # SET FLAGS HERE
            self.pointer += 2
        else:
            print '%04x : add\t%s, %s' % (self.pointer, rd, rr)

    def andi(self, args, print_line):
        self.common_logic('andi', operator.__and__, args, print_line)

    def bld(self, args, print_line):
        (rd, b) = args
        if not print_line:
            value = self.port_vals['3f']
            if self.check_bit(value, 6):
                self.set_bit(self.reg_vals[rd], b)
            else:
                self.clear_bit(self.reg_vals[rd], b)
            self.pointer += 2
        else:
            print '%04x : bst\t%s, %s' % (self.pointer, rd, b)

    def brcc(self, args, print_line):
        self.common_branch('brcc', 128, args, print_line)

    def brne(self, args, print_line):
        self.common_branch('brne', 128, args, print_line)

    def bst(self, args, print_line):
        (rd, b) = args
        if not print_line:
            value = self.reg_vals[rd]
            if self.check_bit(value, b):
                self.sreg_set('t')
            else:
                self.sreg_clear('t')
            self.pointer += 2
        else:
            print '%04x : bst\t%s, %s' % (self.pointer, rd, b)

    def cbi(self, args, print_line):
        self.common_checkio('sbic', args, print_line)

    def cli(self, no, print_line):
        if not print_line:
            self.sreg_clear('i')
            self.pointer += 2
        else:
            print '%04x : cli' % (self.pointer, )

    def clr(self, rd, print_line):
        if not print_line:
            self.sreg_set('z')
            self.sreg_clear(('n', 'v', 's'))
            self.reg_vals[rd] = 0
            self.pointer += 2
        else:
            print '%04x : clr\t%s' % (self.pointer, rd)

    def dec(self, rd, print_line):
        if not print_line:
            value = self.reg_vals[rd]
            value -= 1
            if value == -1:
                value = 255
            self.reg_vals[rd] = value
            bval = self.int2bin(value, 8)[::-1]

            self.sreg_change('s', self.sreg_check('n') ^ self.sreg_check('v') and self.set_bit or self.clear_bit)
            self.sreg_change('v', value == 127 and self.set_bit or self.clear_bit)
            self.sreg_change('n', bval[7] == 1 and self.set_bit or self.clear_bit)
            self.sreg_change('z', value == 0 and self.set_bit or self.clear_bit)
            self.pointer += 2
        else:
            print '%04x : dec\t%s' % (self.pointer, rd)

    def in_op(self, args, print_line):
        (rd, a) = args
        key = '%02x' % a
        value = self.port_vals[key]
        if not print_line:
            self.reg_vals[a] = value
            self.pointer += 2
        else:
            print '%04x : in\t%s, $%02x' % (self.pointer, rd, a)

    def ldi(self, args, print_line):
        (rd, k) = args
        if not print_line:
            self.reg_vals[rd] = k
            self.pointer += 2
        else:
            print '%04x : ldi\t%s, 0x%02X' % (self.pointer, rd, k)

    def mov(self, args, print_line):
        (rd, rr) = args
        if not print_line:
            self.reg_vals[rd] = self.reg_vals[rr]
            self.pointer += 2
        else:
            print '%04x : mov\t%s, %s' % (self.pointer, rd, rr)

    def or_op(self, args, print_line):
        (rd, rr) = args
        if not print_line:
            self.reg_vals[rd] |= self.reg_vals[rr]
            # SET FLAGS HERE
            self.pointer += 2
        else:
            print '%04x : or\t%s, %s' % (self.pointer, rd, rr)

    def ori(self, args, print_line):
        self.common_logic('ori', operator.__or__, args, print_line)

    def out(self, args, print_line):
        (a, rr) = args
        value = self.reg_vals[rr]
        key = '%02x' % a
        if not print_line:
            self.port_vals[key] = value
            self.pointer += 2
        else:
            print '%04x : out\t$%02x, %s' % (self.pointer, a, rr)

    def pop(self, rd, print_line):
        if not print_line:
            self.reg_vals[rd] = self.stack.pop()
            self.pointer += 2
        else:
            print '%04x : pop\t%s' % (self.pointer, rd)

    def push(self, rr, print_line):
        if not print_line:
            self.stack.append(self.reg_vals[rr])
            self.pointer += 2
        else:
            print '%04x : push\t%s' % (self.pointer, rr)

    def rcall(self, args, print_line):
        (k, is_negative) = args
        if is_negative:
            k -= 4096
        if not print_line:
            # SET FLAGS HERE
            self.stack.append(self.pointer)
            self.pointer += 2 * k + 2
        else:
            print '%04x : rcall\t%04x' % (self.pointer, self.pointer + 2 * k + 2)

    def ret(self, no, print_line):
        if not print_line:
            self.pointer = self.stack.pop()
            self.pointer += 2
        else:
            print '%04x : ret' % (self.pointer, )

    def reti(self, no, print_line):
        if not print_line:
            self.sreg_set('i')
            self.pointer = self.stack.pop()
        else:
            print '%04x : reti' % (self.pointer, )

    def rjmp(self, args, print_line):
        (k, is_negative) = args
        if is_negative:
            k -= 4096
        if not print_line:
            self.pointer += 2 * k + 2
        else:
            print '%04x : rjmp\t%04x' % (self.pointer, self.pointer + 2 * k + 2)

    def rol(self, args, print_line):
        (rd, rr) = args
        value = self.reg_vals[rd]
        if not print_line:
            func = self.clear_bit
            if self.check_bit(value, 7):
                func = self.set_bit
            self.reg_vals[rd] = func(value << 1, 0) & 255
            # SET FLAGS HERE
            self.pointer += 2
        else:
            print '%04x : rol\t%s' % (self.pointer, rd)

    def ror(self, rd, print_line):
        if not print_line:
            func = self.clear_bit
            if self.check_bit(self.reg_vals[rd], 0):
                func = self.set_bit
            self.reg_vals[rd] >> 1
            func(self.reg_vals[rd], 7)
            # SET FLAGS HERE
            self.pointer += 2
        else:
            print '%04x : rol\t%s' % (self.pointer, rd)

    def sbic(self, args, print_line):
        self.common_checkio('sbic', args, print_line)

    def sbrs(self, args, print_line):
        (rr, b) = args
        if not print_line:
            if self.check_bit(self.reg_vals[rr], b):
                self.pointer += 2
            self.pointer += 2
        else:
            print '%04x : sbrs\t%s, %s' % (self.pointer, rr, b)

    def sei(self, args, print_line):
        if not print_line:
            self.sreg_set('i')
            self.pointer += 2
        else:
            print '%04x : sei' % (self.pointer, )
