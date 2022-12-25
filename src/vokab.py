from collections import OrderedDict, namedtuple
import re
import datetime
import logging


logger = logging.getLogger(__name__)


DateSection = namedtuple("DateSection", ["date", "header_start", "header_end", "section_start", "section_end"])
re_dates_headers = re.compile(u'# ([0-9]{1,2}\.[0-9]{1,2}.[0-9][0-9])\n')
re_type_headers = re.compile(u'\n\[(\w+)\]\n')
re_vocab_lines = re.compile(u"(.+?)\s+---\s+(.+)")


def process_file(file_content):
    # split file by 'date' section
    splitted_file = re.split(re_dates_headers, file_content)[1:]
    # extract all dates (following file's order)
    dates = splitted_file[0::2]
    dates = list(map(lambda x: datetime.datetime.strptime(x, "%d.%m.%y").date(), dates))
    # extract each 'date' section's content and process it
    contents = splitted_file[1::2]
    contents = list(map(process_date_section, contents))
    # sort the file content by date
    indexes = list(range(len(dates)))
    indexes.sort(key=dates.__getitem__)
    dates = map(dates.__getitem__, indexes)
    contents = map(contents.__getitem__, indexes)

    return dates, contents


def process_date_section(content):
    # split content by 'type' section
    splitted_content = re.split(re_type_headers, content)[1:]
    # extract types (following file's order)
    types = splitted_content[0::2]
    # extract each 'type' section's content and process it
    contents = splitted_content[1::2]
    contents = list(map(process_type_section, contents))
    # sort the date content by type's alphabetical order
    indexes = list(range(len(types)))
    indexes.sort(key=types.__getitem__)
    types = map(types.__getitem__, indexes)
    contents = map(contents.__getitem__, indexes)

    return OrderedDict(zip(types, contents))


def process_type_section(content):
    return [
        (m.group(1), m.group(2))
        for m in  re.finditer(re_vocab_lines, content)
    ]  # list of 2-tuples


def write_date_section(f, content):
    for _type, type_content in content.items():
        f.write(f"[{_type}]\n")
        write_type_content(f, type_content)
    f.write('\n\n')


def write_type_content(f, content):
    maxi = max(len(left) for left, _ in content)
    for left, right in content:
        f.write(f"{left.ljust(maxi)}  ---  {right}\n")
    f.write('\n')


class Vokab(OrderedDict):
    def __init__(self, f):
        file_content = f.read()
        super().__init__(zip(*process_file(file_content)))
        self._today = datetime.date.today()

    def to_file(self, f):
        for date, content in self.items():
            f.write(f"# {date:%d.%m.%y}\n")
            f.write("\n")
            write_date_section(f, content)

    def add(self, results):
        if self._today not in self:
            self[self._today] = OrderedDict()
        for section_name in results:
            if section_name not in self[self._today]:
                self[self._today][section_name] = []
            for line in results[section_name]:
                self[self._today][section_name].append((line['de'], line['fr']))


def display(results):
    for section_name in results:
        print(f"# {section_name}")
        max_length = max(len(line['de']) for line in results[section_name])
        for line in results[section_name]:
            print(f"{line['de'].ljust(max_length)}  --  {line['fr']}")


if __name__ == '__main__':
    from leo import search
    from sys import argv

    with open("./debug.md", "r") as f:
        v = Vokab(f)

    results = search(argv[1])

    display(results)
    v.add(results)

    with open('./debug.md', "w") as f:
        v.to_file(f)
