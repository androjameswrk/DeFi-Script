import os
import glob
import csv
import tkinter as tk
from tkinter import messagebox
import subprocess
from collections import Counter
import shutil
import logging
import re

def clean_data():
    output_rows = []
    download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
    output_folder = os.path.join(download_path, 'label')
    error_folder = os.path.join(output_folder, 'error_files')
    csv_files = glob.glob(os.path.join(download_path, 'arkham_txns*.csv'))
    first_word_counter = Counter()
    error_files = []

    logging.basicConfig(filename=os.path.join(download_path, 'clean_data.log'), level=logging.ERROR,
                        format='%(asctime)s %(message)s')

    def clean_entity(entity):
        if entity:
            # Remove parentheses and text inside them
            entity = re.sub(r'\(.*?\)', '', entity).strip()
            # Skip or return None for "opensea user"
            if "opensea user" in entity.lower():
                return None
        return entity

    def get_first_word(entity):
        cleaned_entity = clean_entity(entity)
        return cleaned_entity.split()[0] if cleaned_entity else ''

    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', newline='') as f:
                reader = csv.reader(f)
                header = next(reader)
                from_address_idx = header.index('fromAddress')  
                from_label_idx = header.index('fromLabel')
                to_address_idx = header.index('toAddress')
                to_label_idx = header.index('toLabel')
                chain_idx = header.index('chain')

                for row in reader:
                    from_address = row[from_address_idx]
                    from_label = row[from_label_idx]
                    to_address = row[to_address_idx]
                    to_label = row[to_label_idx]
                    chain = row[chain_idx]

                    # Skip rows where fromLabel or toLabel is "opensea user"
                    if clean_entity(from_label) is None or clean_entity(to_label) is None:
                        continue

                    if from_address != from_label:
                        first_word_counter[get_first_word(from_label)] += 1
                    if to_address != to_label:
                        first_word_counter[get_first_word(to_label)] += 1
        except Exception as e:
            logging.error(f"Error processing file {csv_file}: {e}")
            error_files.append(csv_file)

    for csv_file in csv_files:
        if csv_file in error_files:
            continue

        try:
            with open(csv_file, 'r', newline='') as f:
                reader = csv.reader(f)
                header = next(reader)
                from_address_idx = header.index('fromAddress')  
                from_label_idx = header.index('fromLabel')
                to_address_idx = header.index('toAddress')
                to_label_idx = header.index('toLabel')
                chain_idx = header.index('chain')

                for row in reader:
                    from_address = row[from_address_idx]
                    from_label = row[from_label_idx]
                    to_address = row[to_address_idx]
                    to_label = row[to_label_idx]
                    chain = row[chain_idx]

                    # Skip rows where fromLabel or toLabel is "opensea user"
                    if clean_entity(from_label) is None or clean_entity(to_label) is None:
                        continue

                    if from_address != from_label and first_word_counter[get_first_word(from_label)] > 10:
                        output_rows.append([from_address, clean_entity(from_label), chain, 'defi'])
                    if to_address != to_label and first_word_counter[get_first_word(to_label)] > 10:
                        output_rows.append([to_address, clean_entity(to_label), chain, 'defi'])
        except Exception as e:
            logging.error(f"Error processing file {csv_file}: {e}")
            error_files.append(csv_file)

    output_rows = list(set(map(tuple, output_rows)))

    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(error_folder, exist_ok=True)

    output_csv = os.path.join(output_folder, 'consolidatedarkham.csv')
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['address', 'entity', 'chain', 'category'])
        writer.writerows(output_rows)

    for csv_file in csv_files:
        if csv_file in error_files:
            shutil.move(csv_file, error_folder)
        else:
            os.remove(csv_file)

    root = tk.Tk()
    root.withdraw()

    row_count = len(output_rows)

    messagebox.showinfo('Complete', 'Finished consolidating CSVs! {} rows written. Output file: {}'.format(row_count, output_csv))

    result = messagebox.askquestion('Open File', 'Open output CSV file?')

    if result == 'yes':
        if os.name == 'nt':  # For Windows
            os.startfile(output_csv)
        elif os.name == 'posix':  # For macOS and Linux
            subprocess.call(('xdg-open', output_csv) if os.uname().sysname != 'Darwin' else ('open', output_csv))

if __name__ == "__main__":
    clean_data()
