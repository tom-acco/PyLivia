import subprocess

class RigCTL(object):
    def __init__(self, rig_file = None, model = None):
        self.rig_file = rig_file
        self.model = model

    def _run(self, cmd):
        base = ["rigctl", "-r", self.rig_file, "-m", self.model]

        if type(cmd) is list:
            run = base + cmd
        else:
            run = base + [cmd]

        result = subprocess.run(run, capture_output=True)

        return result.stdout.decode("utf-8").replace("\n", "")

    def get_freq(self):
        return self._run(["f"])
    
    def set_ptt(self, arg = False):
        if type(arg) is bool:
            if arg:
                return self._run(["T", "1"])
            else:
                return self._run(["T", "0"])