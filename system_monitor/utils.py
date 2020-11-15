import psutil
import time
import multiprocessing
from IPython.display import clear_output
from collections import deque
import matplotlib.pyplot as plt


class SystemMonitorProcess:
    def __init__(self, start_timestamp, update_interval=0.1):
        self.update_interval = update_interval
        self.cpu_nums = psutil.cpu_count()
        self.max_mem = psutil.virtual_memory().total
        self.sysCpuLogs = deque()
        self.sysMemLogs = deque()
        self.timeLogs = deque()
        self.start_time = start_timestamp

    def get_system_info(self):
        cpu_percent = psutil.cpu_percent(interval=self.update_interval, percpu=False)
        mem_percent = float(psutil.virtual_memory().used) / self.max_mem * 100
        return cpu_percent, mem_percent
        
    def monitor(self, logs):
        while True:
            time.sleep(self.update_interval)
            sCpu, sMem = self.get_system_info()  
            self.sysCpuLogs.append(sCpu)
            self.sysMemLogs.append(sMem)
            self.timeLogs.append(time.time() - self.start_time)
            logs.update({
                'sysCpuLogs': self.sysCpuLogs,
                'sysMemLogs': self.sysMemLogs,
                'time': self.timeLogs
            })
            

class SystemMonitor:
    def __init__(self, update_interval=0.1):
        self.graph = None
        self.update_interval = update_interval
        self.max_mem = psutil.virtual_memory().total
        self.start_timestamp = time.time()
        self.msgs = []
        self.logs = multiprocessing.Manager().dict()
        
        self.n_cpus = psutil.cpu_count()
        cpu_clock = psutil.cpu_freq()
        self.cpu_clock = cpu_clock.current/(2**10)
    
    def monitor(self):
        self.graph = SystemMonitorProcess(self.start_timestamp, self.update_interval)
        self.graph.monitor(self.logs)
        
    def annotate(self, msg):
        self.msgs.append([time.time() - self.start_timestamp, msg])
        
    def plot(self):
        logs = self.logs
        if not 'sysCpuLogs' in logs:
            print('No data yet.')
            return
        x_len = min([len(list(logs['time'])), len(logs['sysCpuLogs']), len(logs['sysMemLogs'])])
        xvals = range(int(max(logs['time'])))
        
        fig = plt.figure(figsize=(20,7))
        plt.ylabel('usage (%)')
        
        ax = plt.axes()
        ax.set_xlabel('running time (s)')
        ax.set_xticks(xvals)
        ax.set_xticklabels(xvals)
        
        ax3 = ax.twiny()
        ax3.set_xlabel('running time (%)')
        
        ax2 = ax.twiny()
        ax2.plot(list(logs['time'])[:x_len], list(logs['sysCpuLogs'])[:x_len], ".--", label=f"cpu {self.n_cpus}x {self.cpu_clock:0.1f}GHz")
        ax2.plot(list(logs['time'])[:x_len], list(logs['sysMemLogs'])[:x_len], ".--", label=f"mem {self.max_mem/(8**10):0.1f} GBs")
        ax2.set_xticks([msg[0] for msg in self.msgs])
        ax2.set_xticklabels([msg[1] for msg in self.msgs], rotation=90)
        ax2.tick_params(axis='x', which='major', pad=25)

        ax2.legend(loc='best')
        

if __name__ == "__main__":        
	sm = SystemMonitor(0.1) # polling frequency
	logs = multiprocessing.Manager().dict()
	smp = multiprocessing.Process(target=sm.monitor)
	smp.start()
	time.sleep(2)
	sm.annotate('<annotation to add>')
	time.sleep(2)
	print('Final plot:')
	sm.plot() # shows plot
	smp.terminate() # kills the system monitor
