'''This class is built to support multi-threading for the various scans
conducted by Host and Network objects. Most of this class is agnostic to
the type of multithreading, and by adding another scan type scenario to the
scan target method you could upgrade this to multithreading many types of
activities.'''
from asyncio.subprocess import DEVNULL
import threading
import platform
import subprocess
from queue import Queue
import socket

class ScanThreader:
    '''The class recognizes one of two scan types, Ping Sweep or Port Scan.
    If the user designates the desired number of threads that is prioritized,
    but if not then it takes the number of targets being scanned (either hosts
    or ports) and divides by two. During testing, if the number of threads
    exceeds what the system can handle the scan is unaffected outside of being
    throttled by the operating system itself. If the threads is set manually to
    a low number (such as less than 100 for a scan on 5000 ports), then the scan
    will be quite slow. Anything over 1000-2000 on most systems just maxes out
    what the system itself is capable of.'''
    def __init__(self, scan_type, scan_items, num_threads, verbosity):
        self.scan_type = scan_type
        self.scan_items = scan_items
        self.num_threads = num_threads or int((len(scan_items)+1)/2)
        self.verbosity = verbosity

        self.queue = Queue()
        self.scan_results = set()

        #so that it has to run once, instead of per thread
        if self.scan_type == "Ping Sweep":
            self.param = '-n' if platform.system().lower()=='windows' else '-c'

    def queue_scan(self):
        '''Queue's the targets for the threading'''
        for item in self.scan_items:
            self.queue.put(item)

    def scan_target(self, target, host, timeout):
        '''Core functionality for handling a singular port scan, or a singular
        ping to a host.'''
        if self.scan_type == 'Port Scan':
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                try:
                    sock.connect((host, target))
                    self.scan_results.add(target)
                    return True
                except socket.error:
                    self.scan_results.discard(target)
                    return False
        elif self.scan_type == 'Ping Sweep':
            command = ['ping', self.param, '1', target]
            with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=DEVNULL) as process:
                data = process.communicate()[0].decode()
                if ('unreachable' not in data and 'Request timed out' not in data
                or 'bytes from' in data):
                    self.scan_results.add(target)
                    return True
                self.scan_results.discard(target)
                return False
        return "Scan type malformed"

    def scan_thread(self, host, timeout):
        '''Creates an actual thread which calls the scan'''
        while not self.queue.empty():
            target = self.queue.get()
            if self.scan_type == 'Port Scan':
                up_string = f'[+] Port {target} on {host} is open'
                down_string = f'[-] Port {target} on {host} is closed or filtered'
            elif self.scan_type == 'Ping Sweep':
                up_string = f'[+] Host {target} is up'
                down_string = f'[-] Host {target} is not responding to pings'

            if self.scan_target(target, host, timeout) and self.verbosity >= 1:
                print(up_string)
            else:
                if self.verbosity >= 2:
                    print(down_string)

    def scan(self, host=None, timeout=1):
        '''Creates the threads and then starts them, then waits for threads to
        finish then returns results'''
        self.queue_scan()
        thread_list = []

        for thrd in range(self.num_threads):
            if self.verbosity > 2:
                print(f'Creating thread {thrd}...')
            thread = threading.Thread(target=self.scan_thread,
                                    kwargs={'host':host, 'timeout':timeout})
            thread_list.append(thread)

        for thread in thread_list:
            thread.start()

        for thread in thread_list:
            thread.join()

        return self.scan_results
