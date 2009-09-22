# -*- coding: utf-8 -*-
# (c) 2009 Ruslan Popov <ruslan.popov@gmail.com>

ports = {'03': 'ADCSRB', '04': 'ADCL', '05': 'ADCH',  '06': 'ADCSRA',
         '07': 'ADMUX',  '08': 'ACSR', '14': 'DIDR0', '15': 'PCMSK',  
         '16': 'PINB',   '17': 'DDRB', '18': 'PORTB', '1C': 'EECR',
         '1D': 'EEDR',
         '26': 'CLKPR', '28': 'GRCCR',
         '32': 'TCNT0', '39': 'TIMSK0',
         '3d': 'SPL',
         '3f': 'SREG' }

mnemonics = [
    ('add', '^000011(?P<ra>[01]{1})(?P<rd>[01]{5})(?P<rb>[01]{4})$', 'rd_rr'),
    ('and', '^001000(?P<ra>[01]{1})(?P<rd>[01]{5})(?P<rb>[01]{4})$', 'rd_rr'),
    ('andi', '^0111(?P<ka>[01]{4})(?P<rd>[01]{4})(?P<kb>[01]{4})$', 'rd_k'),
    ('bld', '^1111100(?P<rd>[01]{5})0(?P<b>[01]{3})$', 'rd_b'),
    ('brcc', '^111101(?P<k>[01]{7})000$', 'k6'),
    ('brcs', '^111100(?P<k>[01]{7})000$', 'k6'),
    ('breq', '^111100(?P<k>[01]{7})001$', 'k6'),
    ('brne', '^111101(?P<k>[01]{7})001$', 'k6'),
    ('bst', '^1111101(?P<rd>[01]{5})0(?P<b>[01]{3})$', 'rd_b'),
    ('cbi', '^10011000(?P<a>[01]{5})(?P<b>[01]{3})$', 'a_b'),
    ('cli', '^(?P<op>1001010011111000)$', None),
    ('com', '^1001010(?P<rd>[01]{5})0000$', 'rd'),
    ('cpi', '^0011(?P<ka>[01]{4})(?P<rd>[01]{4})(?P<kb>[01]{4})$', 'rd_k'),
    ('dec', '^1001010(?P<rd>[01]{5})1010$', 'rd'),
    ('eor', '^001001(?P<ra>[01]{1})(?P<rd>[01]{5})(?P<rb>[01]{4})$', 'rd_rr'),
    ('in', '^10110(?P<aa>[01]{2})(?P<rd>[01]{5})(?P<ab>[01]{4})$', 'rd_a'),
    ('ldi', '^1110(?P<ka>[01]{4})(?P<rd>[01]{4})(?P<kb>[01]{4})$', 'rd_k'),
    ('mov', '^001011(?P<ra>[01]{1})(?P<rd>[01]{5})(?P<rb>[01]{4})$', 'rd_rr'),
    ('or', '^001010(?P<ra>[01]{1})(?P<rd>[01]{5})(?P<rb>[01]{4})$', 'rd_rr'),
    ('ori', '^0110(?P<ka>[01]{4})(?P<rd>[01]{4})(?P<kb>[01]{4})$', 'rd_k'),
    ('out', '^10111(?P<aa>[01]{2})(?P<rr>[01]{5})(?P<ab>[01]{4})$', 'a_rr'),
    ('pop', '^1001000(?P<rd>[01]{5})1111$', 'rd'),
    ('push', '^1001001(?P<rd>[01]{5})1111$', 'rd'),
    ('rcall', '^1101(?P<k>[01]{12})$', 'k'),
    ('ret', '^(?P<op>1001010100001000)$', None),
    ('reti', '^(?P<op>1001010100011000)$', None),
    ('rjmp', '^1100(?P<k>[01]{12})$', 'k'),
    ('rol', '^000111(?P<rd>[01]{10})$', 'rd'),
    ('ror', '^1001010(?P<rd>[01]{5})0111$', 'rd'),
    ('sbi', '^10011010(?P<a>[01]{5})(?P<b>[01]{3})$', 'a_b'),
    ('sbic', '^10011001(?P<a>[01]{5})(?P<b>[01]{3})$', 'a_b'),
    ('sbrc', '^1111110(?P<rr>[01]{5})0(?P<b>[01]{3})', 'rr_b'),
    ('sbrs', '^1111111(?P<rr>[01]{5})0(?P<b>[01]{3})', 'rr_b'),
    ('sei', '^(?P<op>1001010001111000)$', None),
    ]

logics = {
    'rd_rr': (('ra', 'rb', 'rd'),
              lambda addr, ra, rb, rd: ('r%s' % int(rd,2), 
                                        'r%s' % int('%s%s' % (ra, rb),2))),
    'rd_k': (('ka', 'kb', 'rd'),
             lambda addr, ka, kb, rd: ('r%s' % (int(rd,2) + 16), 
                                       '%s%s' % (ka, kb))),
    'rd_b': (('rd', 'b'),
             lambda addr, rd, b: ('r%s' % int(rd,2), int(b,2))),
    'k': (('k',),
          lambda addr, k: '0x%04x' % (k.startswith('1') \
                                          and (addr - (2**len(k) + 2 - (int(k,2))) ) \
                                          or  (addr + (2 * int(k,2) + 2))
                                      )),
    'k6': (('k',),
           lambda addr, k: '0x%04x' % (k.startswith('1') \
                                           and (addr + 2 - 2 * (2**len(k) - (int(k,2))) ) \
                                           or  (addr + (2 * int(k,2) + 2))
                                       )),
    'a_b': (('a', 'b'),
            lambda addr, a, b: ('r%s' % int(a,2), int(b,2))),
    'rd': (('rd',),
           lambda addr, rd: 'r%s' % int(rd,2)),
    'rd_a': (('aa', 'ab', 'rd'),
             lambda addr, ka, kb, rd: ('r%i' % (int(rd,2)), 
                                 '0x%02x' % int('%s%s' % (ka, kb),2))),
    'a_rr': (('aa', 'ab', 'rr'),
             lambda addr, aa, ab, rr: ('0x%02x' % int('%s%s' % (aa, ab), 2), 
                                 'r%s' % int(rr,2))),
    'rr_b': (('rr', 'b'),
             lambda addr, rr, b: ('r%i' % (int(rr,2)), int(b,2)))
}
