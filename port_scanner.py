'''
This program is designed to conduct ping scans to check whether hosts are alive,
and TCP scans to check whether specific ports are open on hosts. Each of the scan
types is multithreaded for speed, and the default behavior with a port scan is to
first conduct a ping scan so that port scans aren't being conducted on hosts that
are not alive. Various arguments exist to slightly modify various behaviors,
including the output folder and filename, timeout for port scans, verbosity of the
terminal output (doesn't affect file output), the number of threads to create for
the scans (the default is to take the # of targets and divide by 2), the -s or
--skip option for skipping the ping sweep preceeding the port scan and force the
scan on all provided hosts, and finally an option to conduct the scan continuously,
given N number of seconds, and report whether or not there were any changes in the
scan results. The host(s) and port(s) parse a variety of user inputs including
comma separated, ranges (i.e. 192.168.1.1-10, or 192.168.1-10.5), and CIDR notation,
or any combination therein. Additionally, ports can be supplied as comma separated,
ranges, or a combination.
'''
import argparse
import os
import time
from datetime import datetime
from network import Network
from file_manager import FileManager

def main():
    '''Main function basically just sets up args, then instantiates the other
    classes and uses just a touch of logic to manage the continuous looping'''

    example_text = '''
    Examples:

    [ Conduct ping sweep on network 192.168.1.0/24 and google.com ]
    port_scanner.py 192.168.1.0/24,google.com

    [ Check port 80 on hosts in network 192.168.1.0/24 with unique directory/filename ]
    port_scanner.py 192.168.1.0/24 -p 80 -pa /home/user/Desktop -o my_port_scan.txt

    [ Check ports on list of hosts and increase verbosity of output ]
    port_scanner.py 192.168.1.1-10/24,127.0.0.1,mydomain.com -p 21-23,80,8000 -v 1

    [ Conduct continuous scans (every N seconds) on a specific host and skip initial ping sweep ]
    port_scanner.py localhost -p 8080 -s -c 15
    '''

    # Setting up clean argument parsing with argparser
    parser = argparse.ArgumentParser(description="Given a host, conducts "
                                    + "ping sweeps and port scans.",
                                     epilog=example_text,
                                     formatter_class=argparse.
                                     RawDescriptionHelpFormatter)

    # positional arguments
    parser.add_argument('hosts', metavar='<host(s)>', type=str,
                        help='Enter the host(s) to run the scan against')

    # options
    parser.add_argument('-p', '--ports', type=str, nargs='?',
                        help='Enter the port(s) to scan')
    parser.add_argument('-pa', '--path', type=str, nargs='?',
                        help='Set output directory', default=(os.getcwd()))
    parser.add_argument('-o', '--outfile', type=str, nargs='?',
                        help='Adjust output file name',
                        default=f'{datetime.now().strftime("%d_%h_%y_%H-%M-%S")}_scan.txt')
    parser.add_argument('-t', '--timeout', type=float, nargs='?',
                        help='Set timeout for each port scans', default=1)
    parser.add_argument('-v', '--verbosity', type=int, nargs='?', default=0,
                        help='Increase the verbosity of scan output, 0-3')
    parser.add_argument('-n', '--num_threads', type=int, nargs='?',
                        help='The number of targets to scan at a time')
    parser.add_argument('-s', '--skip', action='store_true',
                        help='Skip the initial ping check for port scans')
    parser.add_argument('-c', '--continuous', type=int, nargs='?',
                        help='Scan every N seconds and report changes, '
                        + 'if scan takes longer than the provided seconds '
                        + 'then it scans without pause')

    args = parser.parse_args()

    # Simply completes the appropriate scan and returns results
    # This is a method so it's repeatable if the -c flag is used
    # The only mandatory argument is hosts, so if no ports are supplied it's
    # assumed that the user wants a ping sweep

    def scan():
        if args.ports:
            network.scan_hosts()
            print(network)
            return str(network)
        print('No ports provided, running Ping Sweep....')
        sweep_scan = network.ping_sweep()
        print(sweep_scan)
        return sweep_scan

    # build network object
    network = Network(args)

    # If continuous is not used this is the core functionality, it creates a
    # file object, conducts a scan using the network object, and writes the
    # scan to disk, along with printing relevent details to the terminal
    start_time = time.time()
    file = FileManager(args)
    first_scan = scan()
    file.write_file(first_scan)

    # If a continuous scan is requested then the time it took to conduct the
    # scan is factored in, then a new scan is taken, compared to the last one
    # and if there are changes, the changes are displayed to the screen
    # and the file is updated to reflect the latest scan, if there are no changes
    # the file is untouched because it would be overwritten with identical data
    if args.continuous:
        while True:
            elapsed = time.time() - start_time
            if args.continuous > elapsed:
                time_to_wait = args.continuous - elapsed
                if time_to_wait >= 0:
                    print(f'Waiting {time_to_wait:.0f} seconds until the next scan..')
                    time.sleep(time_to_wait)
            start_time = time.time()
            new_scan = scan()
            if not file.compare(new_scan):
                file.report_changes(new_scan)
                file.write_file(new_scan)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('User exited..')
