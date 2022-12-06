import multiprocessing as mp
import time

def a(x):
	
	time.sleep(1)
	print(x)

if __name__ == '__main__':
	
	print(mp.current_process().name)
	print('Processes:', mp.cpu_count())
	processes = []
	for i in range(100):
		processes.append(mp.Process(target = a, args = (i,)))
		processes[-1].start()

	#a('Hello, ')
	#b('world!')
	#p1 = mp.Process(target = a, name = 'p1', args = ('Hello,',))
	#p2 = mp.Process(target = b, name = 'p2', args = ('world!',))
	#p1.start()
	#p2.start()