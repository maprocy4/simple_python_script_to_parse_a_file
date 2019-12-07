#!/usr/bin/python3

import sys
import argparse
import magic
import csv
import regex
import datetime
import shutil
import time
import os

persons = []

class Person:
    __name = ''
    __phone = ''
    __display_name = ''

    def __init__(self, name, phone, display_name):
        self.__name = name
        self.__phone = phone
        self.__display_name = display_name

    def set_name(self, name):
        self.__name = name

    def get_name(self):
        return self.__name

    def set_phone(self, phone):
        self.__phone = phone

    def get_phone(self):
        return self.__phone

    def set_display_name(self, display_name):
        self.__display_name = display_name

    def get_display_name(self):
        return self.__display_name


def parse_entry(entry, entry_assignee, entry_type):
    nice_list = []
    # date, unix timestamp, creator, assignee, description

    datetime_pttrn = regex.compile('\d{1,2}/\d{1,2}/\d{1,2}, \d{1,2}:\d{1,2} [A,P]M')
    date_pttrn = regex.compile('\d{1,2}/\d{1,2}/\d{1,2}')

    date_time = datetime_pttrn.match(entry)
    date_time = date_time.group()

    # create unixtimestamp
    date = date_pttrn.match(entry)
    date = date.group()
    month_pttrn = regex.compile('^\d{1,2}')
    day_pttrn = regex.compile('/\d{1,2}/')
    year_pttrn = regex.compile('\d{1,2}\Z')
    month = month_pttrn.search(date)
    month = int(month.group())
    day = day_pttrn.search(date)
    day = day.group()
    day = int(day.strip('/'))
    year = year_pttrn.search(date)
    year = 2000 + int(year.group())
    dt = datetime.datetime(year, month, day)
    unix_ts = ' ' + str(int(dt.timestamp())) 

    # extract creator
    creator_pttrn = regex.compile('M - .*:')
    creator = creator_pttrn.search(entry)
    creator_disp_name = creator.group()
    creator_disp_name = creator_disp_name.rstrip(':')
    creator_disp_name = creator_disp_name[4:]

    ## creator nice name
    creator_nice_name = ''
    for person in persons:
        if person.get_name() == creator_disp_name:
            creator_nice_name = ' ' + person.get_display_name()

    # assignee nice name
    assignee_nice_name = ''
    if entry_assignee != None:
        for person in persons:
            if person.get_name() == entry_assignee:
                assignee_nice_name = ' ' + person.get_display_name()
    else:
        assignee_nice_name = 'None'

    # description
    please_pttrn = regex.compile('[Pp]lease')
    commastxt_pttrn = regex.compile('".*"')
    
    if entry_type == 'please':
        please = please_pttrn.search(entry)
        please_end = please.end()
        pre_description = entry[please_end:]
        description = pre_description.strip(' ')
        description = ' ' + description
    elif entry_type == 'commas':
        description = commastxt_pttrn.search(entry)
        description = description.group()
        description = ' ' + description.strip('"')
        
    nice_list = [date_time, unix_ts, creator_nice_name, assignee_nice_name, description]

    return nice_list

def get_entry_author(entry):
    dispnm_pttrn = regex.compile('M - .*:')
    entry_author = dispnm_pttrn.search(entry)
    author_disp_name = entry_author.group()
    author_disp_name = author_disp_name.rstrip(':')
    author_disp_name = author_disp_name[4:]

    return author_disp_name

def process_data(dataflnm):
    with open(dataflnm, 'r') as data_file:
        data_reader = csv.reader(data_file, delimiter=',')
        i = 0
        for row in data_reader:
            if i == 0:
                i += 1
            else:
                name = row[0]
                phone = row[1].lstrip(' ')
                disp_name = row[2].lstrip(' ')

                persons.append(Person(name, phone, disp_name))

def process_input(inputflnm, outputflnm):
    entry = ''
    entries = []
    inp_lines = []

    with open(inputflnm, 'r') as input_file:
        for inp_line in input_file:
            if inp_line != '\n':
                inp_lines.append(inp_line)

    date_pttrn = regex.compile('\d{1,2}/\d{1,2}/\d{1,2}')   # 8/21/19

    # new_entry = False
    for inp_line in inp_lines:
        if date_pttrn.match(inp_line):   # new_entry = True
            if entry == '':
                entry = inp_line.rstrip('\n ') + ' '
            else:
                entries.append(entry)

                entry = inp_line.rstrip('\n ') + ' '
        else:
            entry += inp_line.rstrip('\n ') + ' ' 
        
    entries.append(entry)

    with open(outputflnm, 'w') as tmpoutpt_file:
        fields = ['date', ' unix timestamp', ' creator', ' assignee', ' description']
        csv_writer = csv.writer(tmpoutpt_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(fields)

        telnum_pttrn = regex.compile('@\d{11}')
        please_pttrn = regex.compile('[Pp]lease')
        commastxt_pttrn = regex.compile('".*"')
        dtend_pttrn = regex.compile('-\d:')

        entries_num = len(entries)
        i = 0

        for entry in entries:
            nice_list = []

            if dtend_pttrn.search(entry):
                colon_pos_match = dtend_pttrn.search(entry)
                colon_pos = colon_pos_match.start() + 4
                entry_meta = entry[:colon_pos]
                entry_text = entry[colon_pos:]

                telnums = telnum_pttrn.findall(entry_text)

                if len(telnums) == 1 and please_pttrn.search(entry_text) and not commastxt_pttrn.search(entry_text):
                    if i+1 < entries_num:
                        entry_assignee = get_entry_author(entries[i+1])
                        nice_list = parse_entry(entry, entry_assignee, 'please')
                        csv_writer.writerow(nice_list)
                    else:
                        nice_list = parse_entry(entry, None, entry_type='please')
                        csv_writer.writerow(nice_list)
                elif len(telnums) == 1 and not please_pttrn.search(entry_text) and commastxt_pttrn.search(entry_text):
                    if i+1 < entries_num:
                        entry_assignee = get_entry_author(entries[i+1])
                        nice_list = parse_entry(entry, entry_assignee, 'commas')
                        csv_writer.writerow(nice_list)
                    else:
                        nice_list = parse_entry(entry, None, entry_type='commas')
                        csv_writer.writerow(nice_list)
            i += 1

    # copy outputflnm to outputflnm-dd-mm-yyyy.txt
    outputflnm_base = outputflnm[:-4]
    date_str = datetime.datetime.today()
    date_str = date_str.strftime("%d-%m-%Y")
    new_outputflnm = outputflnm_base + '-' + date_str + '.txt'

    shutil.copyfile(outputflnm, new_outputflnm)

    # sleep for 5 seconds
    time.sleep(5)

    # delete initial output file
    os.remove(outputflnm)

    msg = '\nYour file ' + new_outputflnm + ' is ready. Enjoy! ;-) :-)'

    return msg

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', dest='dataflnm', nargs=1, help='data file name', required=True)
    parser.add_argument('-i', dest='inputflnm', nargs=1,  help='input file name', required=True)
    parser.add_argument('-o', dest='outputflnm', nargs=1,  help='output file name pattern', required=True)
    args = parser.parse_args()

    dataflnm = args.dataflnm[0]
    inputflnm = args.inputflnm[0]
    outputflnm = args.outputflnm[0]

    # Check the input file-type, if this is text-file.
    datafltp = magic.from_file(dataflnm)
    inputfltp = magic.from_file(inputflnm)

    if 'text' in datafltp:
        print("Data file type detected: " + datafltp + ". Will try...")
        process_data(dataflnm)
    else:
        print("Data file type detected: " + datafltp + " - don`t know what to do with this. Good luck!") 
        sys.exit(1)

    if 'text' in inputfltp:
        print("\nInput file type detected: " + inputfltp + ". Will try...")
        msg = process_input(inputflnm, outputflnm)
        print(msg)
    else:
        print("\nInput file type detected: " + inputfltp + " - don`t know what to do with this. Good luck!") 
        sys.exit(2)

if __name__ == "__main__":
    main(sys.argv)
