'''This class is meant for representing a single Host within a network.
Including functionality for conducting port scans on that host (using threading),
and parsing the user port input using a similar recursive method as the IPs in a Network'''
import time
from scan_threader import ScanThreader

class Host:
    '''This class is represented by the host's IP address, then the user input for
    ports is cleaned up, and open_ports is initialized as a set to keep track of
    positive results on the port scan'''
    def __init__(self, ip_address, args):
        self.ip_address = ip_address
        self.args = args
        self.ports = clean_up_ports(self.args.ports)
        self.open_ports = set()

    def scan_host(self):
        '''This manages the port scanning by using the multi threader class
        and prints the relevent information along with updating it's own
        open ports'''
        if self.args.verbosity >= 1:
            print(f'Initiating scan on {self.ip_address}...\n' + ('-' * 30))
            start_time = time.time()

        scan = ScanThreader('Port Scan', self.ports,
                            self.args.num_threads, self.args.verbosity)
        self.open_ports = scan.scan(self.ip_address, self.args.timeout)

        if self.args.verbosity >= 1:
            elapsed = time.time() - start_time
            print(f'Scan complete on {self.ip_address} in {elapsed:.2f} seconds')
            if self.open_ports:
                pretty_ports = ', '.join(sorted(set(map(str, self.open_ports))))
                print(f'Open port(s): {pretty_ports}\n')
            else:
                print(f'No open ports detected on {self.ip_address}\n')

    def __str__(self):
        '''Formats the relevent attributes'''
        return_str = f'\nHost {self.ip_address} shows the following ports open: \n'
        return_str += '-' * 30 + "\n"
        if self.open_ports:
            for port in sorted(self.open_ports):
                return_str += f'[+] Port {port} is open\n'
        else:
            return_str += f'Either no open ports on {self.ip_address} or host hasn\'t been scanned'

        return return_str

def clean_up_ports(input_ports):
    '''Uses recursion similar to the IP clean up function to detect indicators
    which may exist in user input and splitting the input up into a set. Then
    converts the items in the set into int's so that the socket connection can
    recognize the port number.'''
    if isinstance(input_ports, str):
        input_ports = set([input_ports])

    output_ports = set()

    for item in input_ports:
        if ',' in item:
            for piece in item.split(','):
                output_ports.update(clean_up_ports(piece))
        elif '-' in item:
            start, stop = item.split('-')
            output_ports.update(range(int(start), int(stop) + 1))
        else:
            output_ports.add(item)
    return set(map(int, output_ports))
