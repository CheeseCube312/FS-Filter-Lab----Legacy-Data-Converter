import os
import sys
import shutil
import glob
import csv
from tqdm import tqdm

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILTERS_DIR = os.path.join(BASE_DIR, 'filters_data')
QE_DIR = os.path.join(BASE_DIR, 'QE_data')
FAILED_DIR = os.path.join(BASE_DIR, 'failed conversions')

# Helper: wide to tall for filters
def convert_filter_file(input_path, output_path):
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            header = next(reader)
            meta_cols = header[:4]
            wavelengths = header[4:]
            # Find the first non-empty row
            for row in reader:
                if row and any(cell.strip() for cell in row):
                    meta = (row[:4] + [''] * 4)[:4]
                    values = (row[4:] + [''] * len(wavelengths))[:len(wavelengths)]
                    break
            else:
                raise ValueError('No data row found')
        # Write tall format
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['Wavelength', 'Transmittance', 'hex_color', 'Manufacturer', 'Name', 'Filter Number'])
            for i, wl in enumerate(wavelengths):
                if i == 0:
                    writer.writerow([wl, values[i], meta[3], meta[2], meta[1], meta[0]])
                else:
                    writer.writerow([wl, values[i], '', '', '', ''])
        return True
    except Exception as e:
        print(f"Failed to convert {input_path}: {e}")
        return False

# Helper: wide to tall for QE
def convert_qe_file(input_path, output_path):
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            header = next(reader)
            channels = []
            data_rows = []
            for row in reader:
                if row and row[0]:
                    # Pad row to at least 3 metadata columns
                    padded = (row[:3] + [''] * 3)[:3]
                    channels.append(padded)
                    # Pad data to match wavelengths
                    data = (row[3:] + [''] * (len(header)-3))[:len(header)-3]
                    data_rows.append(data)
        wavelengths = header[3:]
        # Write tall format
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['Wavelength', 'B', 'G', 'R', 'Manufacturer', 'Name'])
            for i, wl in enumerate(wavelengths):
                vals = [data_rows[0][i] if len(data_rows)>0 else '',
                        data_rows[1][i] if len(data_rows)>1 else '',
                        data_rows[2][i] if len(data_rows)>2 else '']
                if i == 0:
                    writer.writerow([wl] + vals + [channels[0][1], channels[0][2]])
                else:
                    writer.writerow([wl] + vals + ['', ''])
        return True
    except Exception as e:
        print(f"Failed to convert {input_path}: {e}")
        return False


# Helper: recursively find all .tsv files in a directory
def find_tsv_files(root_dir):
    tsv_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith('.tsv'):
                tsv_files.append(os.path.join(dirpath, filename))
    return tsv_files

def get_relative_path(path, base):
    return os.path.relpath(path, base)

if __name__ == '__main__':
    print('Converting files...')
    total = 0
    success = 0
    failed = 0
    failed_files = []
    # Filters
    filter_files = find_tsv_files(FILTERS_DIR)
    for fpath in tqdm(filter_files, desc='Filters'):
        rel_path = get_relative_path(fpath, FILTERS_DIR)
        outpath = fpath  # Overwrite in place
        total += 1
        if convert_filter_file(fpath, outpath):
            success += 1
        else:
            failed_path = os.path.join(FAILED_DIR, rel_path)
            os.makedirs(os.path.dirname(failed_path), exist_ok=True)
            shutil.move(fpath, failed_path)
            failed += 1
            failed_files.append(rel_path)
    # QE
    qe_files = find_tsv_files(QE_DIR)
    for fpath in tqdm(qe_files, desc='Quantum Efficiency'):
        rel_path = get_relative_path(fpath, QE_DIR)
        outpath = fpath  # Overwrite in place
        total += 1
        if convert_qe_file(fpath, outpath):
            success += 1
        else:
            failed_path = os.path.join(FAILED_DIR, rel_path)
            os.makedirs(os.path.dirname(failed_path), exist_ok=True)
            shutil.move(fpath, failed_path)
            failed += 1
            failed_files.append(rel_path)
    print(f'Successfully converted {success}/{total} files')
    print(f'{failed} failed conversions')
    if failed_files:
        print('Failed files:')
        for fname in failed_files:
            print('  ', fname)

    # Clean up: delete failed conversions folder if empty
    def is_dir_empty(path):
        for root, dirs, files in os.walk(path):
            if files:
                return False
        return True
    if is_dir_empty(FAILED_DIR):
        try:
            shutil.rmtree(FAILED_DIR)
            print(f"Deleted empty folder: {FAILED_DIR}")
        except Exception as e:
            print(f"Could not delete {FAILED_DIR}: {e}")

    input('Press Enter to exit...')
