import time
import psutil as p

# print(psutil.cpu_percent())
# print(psutil.virtual_memory().percent)

def display_usage(cpu_percent, mem_percent, files=None, bars=20):
    cpu_usage = (cpu_percent / 100.0)
    cpu_bar = '█' * int(cpu_usage * bars) + '-' * (bars - int(cpu_usage * bars))

    mem_usage = (mem_percent / 100.0)
    mem_bar = '█' * int(mem_usage * bars) + '-' * (bars - int(mem_usage * bars))

    print(f'\rCPU Usage: |{cpu_bar}| {cpu_percent:.2f}%  MEM Usage: |{mem_bar}| {mem_percent:.2f}%  '
            , end='\r')
    # f.write(f'\rCPU: {cpu_percent:.2f}%  MEM: {mem_percent:.2f}%')


# with open('/dev/tty1','wt') as f:
while True:
    display_usage(p.cpu_percent(), p.virtual_memory().percent, None, 30)
    time.sleep(.25)
