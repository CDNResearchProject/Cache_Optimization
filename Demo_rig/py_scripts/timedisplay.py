import time
from time import asctime, localtime

while True:
    t = time.time()
    # time.sleep(1)
    print(f'\r{asctime(localtime(t))}', end='')

