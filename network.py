'''This class is built to handle the concept of a "network." If the requested
scan is just a ping sweep then main calls the ping sweep method, and if a port
scan is requested then this class created a Host object for each address in the
provided network, then calls upon the methods in host to conduct a scan on each
host.'''

import time
import ipaddress
from host import Host
from scan_threader import ScanThreader

class Network:
    '''Host ips is parsed using the clean up function, and hosts is initialized as
    an empty list, to be later populated as a list of Host objects. Similarly, up_hosts
    is initialized to represent the hosts that responded to pings so that Host objects
    aren't created for nonexistent hosts.'''
    def __init__(self, args):
        self.args = args
        self.host_ips = clean_up_ips(args.hosts)
        self.hosts = []
        self.up_hosts = set()

    def scan_hosts(self):
        '''Resets hosts and up_hosts so if the scanning is continuous, repeats
        aren't created, then conducts a ping sweep (if user didn't request to skip
        it) and creates a Host object for all alive hosts, then calls the function
        to conduct port scans, and reports various pieces of useful information
        about the status of the scans'''
        self.hosts = []
        self.up_hosts = set()
        if not self.args.skip:
            print('Initiating ping sweep...')
            if self.args.verbosity >= 1:
                print('Using ping sweep to reduce hosts for port scan.'
                    + 'Use -s or --skip to force port scans on all provided hosts.\n')
            self.ping_sweep()
        else:
            self.up_hosts = self.host_ips
            print('Skipping ping sweep...')

        for addr in self.up_hosts:
            self.hosts.append(Host(addr, self.args))

        if self.up_hosts:
            print(f'Initiating port scan on {len(self.up_hosts)} host(s)...')
            print('-' * 30 + '\n')
            start_time = time.time()

            for host in self.hosts:
                host.scan_host()

            elapsed = time.time() - start_time
            print(f'Scan on {len(self.hosts)} host(s) complete in {elapsed:.2f} seconds\n')

    def ping_sweep(self):
        '''This makes use of the ScanThreader class to push out pings to the hosts
        provided by the user, then reports on status and send the results back'''
        start_time = time.time()
        if self.args.verbosity >= 1 or not self.args.ports:
            print(f'Beginning ping sweep on {len(self.host_ips)} hosts...\n')

        scan = ScanThreader('Ping Sweep', self.host_ips, self.args.num_threads, self.args.verbosity)
        self.up_hosts = scan.scan()

        elapsed = time.time() - start_time
        return_str = f'\nPing sweep complete on {len(self.host_ips)} host\n'
        if self.up_hosts:
            for host in self.up_hosts:
                return_str += f'[+] Host {host} is up\n'
        else:
            return_str += 'All hosts scanned are either down or not responding to pings\n'

        if self.args.verbosity >= 1 and self.args.ports:
            print(f'Scanned {len(self.host_ips)} host(s) in {elapsed:.2f} seconds\n {"-" * 30}\n')
            print('-' * 30 + '\n')
            print(return_str)

        return return_str

    def __str__(self):
        '''Turn information about the network into pretty formatting'''
        return_str = ''
        if self.up_hosts:
            return_str += f'{len(self.host_ips)} host(s) scanned:\n'
        else:
            return_str += 'No hosts detected, cancelling port scan...\n'
        return_str += '-' * 30 + '\n'
        for each_host in self.hosts:
            return_str += str(each_host)
        return return_str

def clean_up_ips(input_ips):
    '''This function is used recursively to parse user input for ips into a usable format.
    A set is used so that duplicates can't be added to the final list and therefore unecessarily
    scanned twice. On each loop the item in the set is searched for a comma, dash, or backslash,
    and if any are found then it's split on the comma, or the range is expanded, or
    a CIDR network is provided using the ipaddress libary. IF any of these indicators are found,
    then a subset is created and recursively sent through the function until finally no items in
    the list flag on any of these indicators and the recursion folds into itself back up to the
    original function call'''
    if isinstance(input_ips, str):
        input_ips = set([input_ips])

    output_ips = set()
    for host in input_ips:
        if ',' in host:
            for item in host.split(','):
                output_ips.update(clean_up_ips(item))
        elif '-' in host:
            octets = host.split('.')
            subnet_request = False
            for octet in octets:
                if '-' in octet:
                    index = octets.index(octet)
                    start, end = octet.split('-')
                    if '/' in end:
                        end, subnet = end.split('/')
                        subnet_request = True
                    octet_range = range(int(start), int(end)+1)
            for octet in octet_range:
                octets[index] = (str(octet) + '/' + subnet) if subnet_request else octet
                output_ips.update(clean_up_ips(f'{octets[0]}.{octets[1]}.{octets[2]}.{octets[3]}'))
        elif '/' in host:
            for addr in ipaddress.IPv4Network(host, strict=False):
                output_ips.add(str(addr))
        else:
            output_ips.add(host)
    return output_ips
