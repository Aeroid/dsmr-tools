import sys

sys.stdout.reconfigure(encoding='latin1')

def read_text_records(filename):
    with open(filename, 'rb') as f:
        records = []
        record = []
        wholefile = f.read().decode('latin1')
        for line in wholefile.splitlines(keepends=True):
            record.append(line)
            if line == '\n':
                records.append(''.join(record))
                record = []

        if record:
            records.append(''.join(record))

        return records

if __name__ == '__main__':
    filename = sys.argv[1]
    records = read_text_records(filename)

    for record in records:
        print(record,end="")
