class ALU(object):

    def __init__(self, *args, **kwargs):
        self.pointer = 0
        self.reg_vals = {}
        self.port_vals = {}
        self.stack = []

        self.flags = {'i': 7, 't': 6, 'h': 5, 's': 4,
                      'v': 3, 'n': 2, 'z': 1, 'c': 0}

    def set_bit(self, x, bitnum):
        """ Sets appropriate bit. """
        return x | 1 << bitnum

    def clear_bit(self, x, bitnum):
        """ Clears appropriate bit. """
        return x & ~(1 << bitnum)

    def check_bit(self, x, bitnum):
        """ Checks if appropriate bit is set. """
        return (x & (1 << bitnum)) != 0

    def sreg_change(self, bit_name, action=None):
        value = self.port_vals['3f']
        bit = self.flags[bit_name]
        self.port_vals['3f'] = action(value, bit)

    def sreg_set(self, bit_name):
        if type(bit_name) is tuple:
            for i in bit_name:
                self.sreg_change(i, self.set_bit)
        else:
            self.sreg_change(bit_name, self.set_bit)

    def sreg_reset(self, bit_name):
        if type(bit_name) is tuple:
            for i in bit_name:
                self.sreg_change(i, self.clear_bit)
        else:
            self.sreg_change(bit_name, self.clear_bit)

    def sreg_check(self, bit_name):
        value = self.port_vals['3f']
        bit = self.flags[bit_name]
        return self.check_bit(value, bit)

    def int2bin(self, n, count=16):
        """ Converts integer to binary representation. """
        return "".join([str((n >> y) & 1) for y in range(count-1, -1, -1)])
