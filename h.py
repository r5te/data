import re
import os
import sys
import threading
import time
from colorama import Fore, Style, init
from pathlib import Path
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor

# Initialize colorama
init(autoreset=True)

def set_cmd_window_size(width, height):
    os.system(f'mode con: cols={width} lines={height}' if os.name == 'nt' else '')

set_cmd_window_size(140, 25)

def LOGO():
    os.system('cls' if os.name == 'nt' else 'clear')
    return fr'''
{Fore.BLUE}
  _    _ _ _       _ 
 | |  | (_) |     | |
 | |__| |_| | __ _| |
 |  __  | | |/ _` | |
 | |  | | | | (_| | |
 |_|  |_|_|_|\__,_|_|

{Fore.BLUE}              By: hilal
    '''

class Filter:
    def __init__(self, web=None, delimiter="|"):
        self.web = web.lower() if web else None  # Optional filter for a specific web
        self.saved_accounts = {}
        self.delimiter = delimiter  # The delimiter to use for splitting
        self.lock = threading.Lock()
        self.process_file()

    def load_files(self):
        while True:
            try:
                files_input = input("Enter DATA Files (comma-separated): ")
                files = [f.strip().strip("'") for f in files_input.split(',')]
                valid_files = []
                for file in files:
                    path = Path(file.strip('"'))  # Remove quotes
                    if path.is_file():
                        valid_files.append(str(path))
                    else:
                        print(f"{Fore.RED}File not found: {path}")
                if valid_files:
                    return valid_files
                else:
                    print(f"{Fore.RED}No valid files found. Please try again.")
            except Exception as e:
                print(f"{Fore.RED}Error reading files: {e}")

    def process_line(self, line):
        if self.delimiter in line:
            parts = line.strip().split(self.delimiter)
            if len(parts) >= 3:
                url = parts[0].strip()
                account = parts[1].strip()
                password = parts[2].strip()

                if self.web is None or self.web in url.lower():
                    with self.lock:
                        if account not in self.saved_accounts:
                            self.saved_accounts[account] = password
                            print(f"{Fore.GREEN}Found: {url}")
                            print(f"{Fore.YELLOW}User: {account}")
                            print(f"{Fore.RED}Pass: {password}")
                            return f"{url}\nUser: {account}\nPass: {password}\n=========================\n"
        return None

    def process_file(self):
        current_dir = Path(__file__).parent
        pool_size = max(4, cpu_count() * 2)
        print(f"{Fore.YELLOW}Using {pool_size} threads for processing...")

        start_time = time.time()

        files = self.load_files()
        results = []
        
        with ThreadPoolExecutor(max_workers=pool_size) as executor:
            for file in files:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    results.extend(executor.map(self.process_line, f))
        
        elapsed_time = time.time() - start_time

        output_file = current_dir / f'{self.web}_extracted_data.txt' if self.web else current_dir / 'extracted_data.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(filter(None, results))

        print(f"{Fore.GREEN}\nProcessing complete. Total accounts saved: {len(self.saved_accounts)}")
        print(f"{Fore.YELLOW}Time taken: {elapsed_time:.2f} seconds")
        print(f"{Fore.YELLOW}Results saved in {output_file}")
        input("Press Enter to exit...")

def main():
    print(LOGO())
    print(f"{Fore.CYAN}Choose an option:")
    print(f"1. Use the tool to analyze data with '|' as the delimiter.")
    print(f"2. Use the tool to analyze data with ':' as the delimiter.")
    
    choice = input(f"{Fore.YELLOW}Enter your choice (1 or 2): ").strip()
    delimiter = "|"

    if choice == '1':
        delimiter = "|"
    elif choice == '2':
        delimiter = ":"
    else:
        print(f"{Fore.RED}Invalid choice. Exiting.")
        sys.exit()

    web = input(f"{Style.RESET_ALL}Enter target site (optional): ").strip()
    Filter(web, delimiter)

if __name__ == "__main__":
    main()
