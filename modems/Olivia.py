import sounddevice
import numpy

from queue import Queue

class OliviaModem(object):
    def __init__(self, sample_rate = 8000, attenuation = 30, preamble = True, centre_freq = 1500, symbols = 32, bandwidth = 1000, callback = None):
        # Set params
        self.sample_rate = sample_rate
        self.attenuation = attenuation
        self.preamble = preamble
        self.centre_freq = centre_freq
        self.symbols = symbols
        self.bandwidth = bandwidth
        self.callback = callback

        ## Number of bits for symbol
        self.spb = int(numpy.log2(self.symbols))

        ## Frequency separation between tones in Hz
        self.fsep = self.bandwidth / self.symbols

        ## Time separation between tones, in samples
        self.wlen = int(numpy.ceil(self.sample_rate / self.fsep))

        ## Buffer containing trail of last symbol, for overlapping
        self.trail = numpy.zeros(self.wlen)

        ## sounddevice InputStream for sample acquisition
        self.inputStream = sounddevice.InputStream(
            samplerate = self.sample_rate,
            blocksize = self.wlen,
            dtype = numpy.float32,
        )

        ## sounddevice OutputStream for sample playback
        self.outputStream = sounddevice.OutputStream(
            samplerate = self.sample_rate,
            blocksize = 64 * self.wlen,
            channels = 1,
            dtype = numpy.float32,
            callback = self.transmit
        )
        
        self.inputStream.start()
        self.outputStream.start()

        self.queue = Queue()

        print(f"Initialised Olivia modulator at {str(self.centre_freq)}Hz, using {str(self.symbols)} tones over {str(self.bandwidth)}Hz")

    def getConfig(self):
        print("----- CONFIG -----")
        print(f"Sample Rate: {self.sample_rate}")
        print(f"Attenuation: {self.attenuation}")
        print(f"Preamble: {self.preamble}")
        print(f"Centre Freq: {self.centre_freq}Hz")
        print(f"Tones: {self.symbols}")
        print(f"Bandwidth: {self.bandwidth}Hz")
        print("------------------")

    def transmit(self, outdata, frames, time, status):
        try:
            data = self.queue.get_nowait()
        except:
            data = None

        outdata[:,0] = data

        if data is not None:
            if self.callback:
                self.callback(state = "Transmitting")
        else:
            if self.callback:
                self.callback(state = "Idle")

    def generatePreamble(self):
        '''
        A preamble is the beginning tail before data transmission.
        But if it doesn't fit in a full block buffer, don't bother.
        '''

        wf = numpy.zeros(64 * self.wlen)
        
        tail = self.generateTail()
        
        if len(tail) < 64 * self.wlen:
            wf[64 * self.wlen - len(tail) : 64 * self.wlen] = tail
        
        return wf
    
    def generateTail(self):
        '''
        A tail is made in this way:
            first tone, last tone, first tone, last tone
        each one lasting 1/4 seconds.
        '''

        pl = int(self.sample_rate / 4)
        t = numpy.arange(0, 1 / 4, 1 / self.sample_rate)
        wf = numpy.zeros(self.sample_rate)
        wf[0 : pl] = self.toneShaper(numpy.sin(2 * numpy.pi * (self.centre_freq - self.bandwidth / 2 + self.fsep / 2) * t) / 2)
        wf[pl : 2 * pl] = self.toneShaper(numpy.sin( 2 * numpy.pi * (self.centre_freq + self.bandwidth / 2 - self.fsep / 2) * t) / 2)
        wf[2 * pl : 3 * pl] = wf[0 : pl]
        wf[3 * pl : 4 * pl] = wf[pl : 2 * pl]

        return wf

    def generateBlock(self, piece):
        '''
        Transmits samples corresponding to a full block.
        '''
        
        wf = numpy.zeros(64 * self.wlen + self.wlen)
        
        # Overlaps trail of last symbol, if any
        wf[0 : self.wlen] += self.trail
        
        # If transmission is being stopped, add trailing tail
        if piece == None:
            if not self.preamble:
                return wf[0 : 64 * self.wlen]
            
            self.trail = numpy.zeros(self.wlen)

            tail = self.generateTail()

            if len(tail) < 64 * self.wlen:
                wf[self.wlen:self.wlen + len(tail)] = tail

            return wf[0 : 64 * self.wlen]
        
        syms = self.prepareSymbols(piece)
        
        for i in range(0, 64):
            # Tone number is symbol number after Gray encoding
            # This minimized error made by mistaking one tone for
            # another one right next to it (1 wrong bit only).
            tone = self.oliviaTone(self.gray(syms[i]))
            wf[self.wlen * i:self.wlen * i + len(tone)] += tone
            
        self.trail = wf[64 * self.wlen : 64 * self.wlen + self.wlen]
        
        return wf[0 : 64 * self.wlen]

    def oliviaTone(self, toneNumber):
        '''
        Tone generator. Creates output waveform for specified tone number.
        '''
        toneFreq = (self.centre_freq - self.bandwidth / 2) + self.fsep / 2 + self.fsep * toneNumber
        t = numpy.arange(0, 2 / self.fsep, 1 / self.sample_rate)
        ph = numpy.random.choice([-numpy.pi / 2, numpy.pi / 2])
        ret = numpy.sin(2 * numpy.pi * toneFreq * t + ph)
        return self.toneShaper(ret)

    def toneShaper(self, toneData):
        '''
        Tone shaping to avoid intersymbol modulation.
        Cosine coefficients are fixed and can be found in specification.
        '''

        x = numpy.linspace(-numpy.pi, numpy.pi, len(toneData))

        shape = (
            1. + 1.1913785723 * numpy.cos(x)
            - 0.0793018558 * numpy.cos(2 * x)
            - 0.2171442026 * numpy.cos(3 * x)
            - 0.0014526076 * numpy.cos(4 * x)
        )

        return toneData * shape

    def prepareSymbols(self, chars):
        '''
        Transform a block of characters into a block of symbols
        ready for transmission.
        '''

        w = numpy.zeros((self.spb, 64))
        
        # Key is a 64-bit fixed value and can be found in specification.
        #   key = 0xE257E6D0291574EC
        # It is a pseudorandom value and its role is to make the
        # output stream appear random.
        # Here it is decomposed in a bit array for easier use.
        key = numpy.flip(numpy.array(
            [1, 1, 1, 0, 0, 0, 1, 0,
            0, 1, 0, 1, 0, 1, 1, 1,
            1, 1, 1, 0, 0, 1, 1, 0,
            1, 1, 0, 1, 0, 0, 0, 0,
            0, 0, 1, 0, 1, 0, 0, 1,
            0, 0, 0, 1, 0, 1, 0, 1,
            0, 1, 1, 1, 0, 1, 0, 0,
            1, 1, 1, 0, 1, 1, 0, 0]))
        
        # Character to 64-value vector mapping to provide redundancy.
        # Characters are 7-bit (value from 0 to 127)
        # Values from 0 to 63 are mapped by setting nth value to 1
        # Values from 64 to 127 are mapped by setting nth value to -1
        # Every other value in vector is 0.
        for i in range(0, self.spb):
            q = ord(chars[i])
            if q > 127:
                q = 0

            if q < 64:
                w[i, q] = 1
            else:
                w[i, q-64] = -1
            
            # Inverse Walsh-Hadamard Transform to encode redundancy
            w[i,:] = self.ifwht(w[i,:])
            
            # XOR with key to ensure randomness
            # (XOR is made by multiplying with -1 or 1)
            w[i,:] = w[i,:] * (-2 * numpy.roll(key, -13*i)+1)
        
        syms = numpy.zeros((64, self.spb))
        
        # Bit interleaving to spread errors over symbols
        for bis in range(0, self.spb):
            for sym in range(0, 64):
                q = 100*self.spb + bis - sym
                if w[q % self.spb,sym] < 0:
                    syms[sym,bis] = 1

        # Convert to integer to find symbol numbers
        symn = numpy.zeros(64)
        for i in range(0,64):
            symn[i] = self.bits2int(numpy.flip(syms[i]))

        return symn
    
    def ifwht(self, data):
        '''
        Inverse Fast Walsh-Hadamard transform.
        There is a similar ready-made transform in sympy, but its
        output ordering (Hadamard order) is different from the Olivia
        specified one, and it's more efficient to reimplement it
        directly rather than converting the output.
        
        This is a 1:1 translation from the Olivia C++ reference
        implementation.
        '''

        step = int(len(data)/2)
        while step >= 1:
            for ptr in range(0, 64, 2*step):
                for ptr2 in range(ptr, step+ptr):
                    bit1 = data[ptr2]
                    bit2 = data[ptr2+step]
                    
                    newbit1 = bit1
                    newbit1 = newbit1 - bit2
                    newbit2 = bit1
                    newbit2 = newbit2 + bit2
                    
                    data[ptr2] = newbit1
                    data[ptr2+step] = newbit2
            step = int(step/2)
        return data

    def bits2int(self, A):
        '''
        Utility function to transform a bit array to an integer.
        '''

        return int(str(A).replace(".", "").replace(",", "").replace(" ", "")
        .replace("[", "").replace("]", ""), 2)

    def gray(self, n):
        '''
        Utility function to calculate Gray encoding of an integer value
        '''

        n = int(n)
        return n ^ (n >> 1)

    def send(self, message):
        # Splits message in pieces, padding last one.
        # Then puts the pieces in transmission queue.
        self.queue.put(self.generatePreamble() / self.attenuation)

        for i in range(0, len(message), self.spb):
            piece = message[i : i + self.spb]

            while len(piece) < self.spb:
                piece = piece + "\0"

            self.queue.put(self.generateBlock(piece) / self.attenuation)
        
        ## Trailing tail
        self.queue.put(self.generateBlock(None) / self.attenuation)