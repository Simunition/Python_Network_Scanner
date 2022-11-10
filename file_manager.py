'''This class is built for managing the file created by the port scanner.'''
import hashlib
import os
import difflib

class FileManager:
    '''Primariliy the class uses the file path and name either set by default
    or provided by the user. A hash attribute is initialized to simplify the
    comparison of the scan results each time a scan is run when using continuous
    scanning.'''
    def __init__(self, args):
        self.args = args
        self.hash = ''
        self.file_location = os.path.join(self.args.path, self.args.outfile)

    def compare(self, new_scan):
        '''This takes a hash of the incoming scan and simply compares it to
        the hash attribute. If they're the same, the scan results are the same,
        and it returns True. If there's any changes to the scan the hash will change
        and report False.'''
        new_hash = hashlib.md5(new_scan.encode())
        if new_hash.hexdigest() == self.hash:
            print("\nNo changes to scan\n")
            return True
        return False

    def write_file(self, new_scan):
        '''Before writing the file a hash is taken of the scan and saved into the hash
        attribute, because it's marginally simpler and more efficient to hash a
        variable than it is to hash a file. It then writes the first, or latest scan
        to the file. Note this function is only called if the scan results change
        when using continuous scanning.'''
        file_hash = hashlib.md5(new_scan.encode())
        self.hash = file_hash.hexdigest()

        with open(self.file_location, 'w+', encoding='utf-8') as file:
            file.write(new_scan)

    def report_changes(self, new_scan):
        '''This uses the difflib to print out any changes to the scan which may have
        appeared in the latest scan. Again, this method is only called if the scan
        hash changes.'''
        with open(self.file_location, 'r', encoding='utf-8') as file:
            file_text = file.read().splitlines()

        new_scan = new_scan.split('\n')
        new_scan = [item for item in new_scan if item]
        file_text = [item for item in file_text if item]

        print('\nScan changes detected! \nLines beginning with - indicate '
            + 'they are no longer present\nLines beginning with + indicate new additions\n')

        for line in list(difflib.Differ().compare(file_text, new_scan)):
            if line[0] == '-' or line[0] == '+':
                print(line.rstrip('\n'))
        print('\n')
