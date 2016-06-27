#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import getopt


# detect if chinese in word
def contains_zh(word):
    return re.compile(u'[\u4e00-\u9fa5]+').search(word)


# resword is basic unit, save english word and chinese word
class resword_info:
    def __init__(self):
        self.res_id = ''
        self.words = []


    def add_word(self, word):
        if word in self.words:
            return

        # append chinese at tail, and insert english at head
        if contains_zh(word):
            if len(self.words) == 0:
                self.words.append('')
            self.words.append(word)
        else:
            if len(self.words) == 0:
                self.words.append(word)
            else:
                if self.words[0] == '':
                    self.words[0] = word
                else:
                    self.words.insert(0, word)

    def to_string(self):
        str = self.res_id
        return u'%s\t%s' % (self.res_id, '\t'.join(self.words))


# res manager
class res_manager:
    def __init__(self):
        self.reswords = {}
        self.reverse_map = {}  # for map chinese to english


    def add_resword(self, res_id, word):
        if self.reswords.has_key(res_id):
            self.reswords[res_id].add_word(word)
        else:
            ri = resword_info()
            ri.res_id = res_id
            ri.add_word(word)
            self.reswords[res_id] = ri

    def read_line(self, line):
        parts = line.split('\t')
        if len(parts) > 2:
            res_id = parts[0]
            for word in parts[1:]:
                self.add_resword(res_id, word)

    def is_xml_file(self, xml_filename):
        return xml_filename.lower().endswith('.xml')

    def read_xml(self, xml_filename):
        if not self.is_xml_file(xml_filename):
            # print u'%s is not xml file' % (xml_filename)
            return False

        print 'read_xml ' + xml_filename
        fi = open(xml_filename, "r")
        for line in fi.readlines():
            line = line.decode('utf-8').strip()
            # <string name="msg_wifipwd_error">Wrong password</string>
            p = re.compile(u'<string name="([\w\-_]+)">(.*?)</string>')
            m = p.search(line)
            if m:
                self.add_resword(m.group(1), m.group(2))

        fi.close()
        return True

    # read all xml files in dir
    def read_dir(self, dir):
        files = os.listdir(dir)
        for file in files:
            self.read_xml(dir + '\\' + file)

    # export reswords to csv file
    def write_csv(self, csv_filename):
        fo = open(csv_filename, "w")

        for (res_id, resword) in self.reswords.items():
            fo.write(''.encode('utf-8-sig'))
            line = resword.to_string().encode('utf-8')
            fo.write(line)
            fo.write('\n')

        fo.close()
        return True

    # import exist csv file to enhance resword
    def read_csv(self, csv_filename):
        fi = open(csv_filename, "r")
        try:
            for line in fi.readlines():
                line = line.decode('utf-8').strip()
                self.read_line(line)

            return True
        finally:
            fi.close()

        return False

    # for those which has no exist localization word, simply replace "_" with " " as supplement
    def supplement(self):
        for (res_id, ri) in self.reswords.items():
            if (len(ri.words) > 1) and (ri.words[0] == ''):
                # e.g. take_a_picture -> take a picture
                ri.words[0] = res_id.replace('_', ' ')

    # map from chinese to english
    def get_reverse_map(self):
        for (res_id, ri) in self.reswords.items():
            if (len(ri.words) > 1) and (ri.words[0] != '') and (ri.words[1] != ''):
                if contains_zh(ri.words[1]):
                    self.reverse_map[ri.words[1]] = ri.words[0]

    # for those which has no exist localization word, use translated chinese to match english word
    def reverse_supplement(self):
        self.get_reverse_map()

        for (res_id, ri) in self.reswords.items():
            if (len(ri.words) > 1) and (ri.words[0] == '') and (ri.words[1] != ''):
                if self.reverse_map.has_key(ri.words[1]):
                    ri.words[0] = self.reverse_map[ri.words[1]]
                    self.reswords[res_id] = ri

    # apply localization to this xml file and write to another file with ".new" appended
    def apply_to_xml(self, xml_filename):
        print 'apply_to_xml ' + xml_filename

        if not os.path.exists(xml_filename):
            print u'%s is not exist' % (xml_filename)
            return False

        fi = open(xml_filename, "r")
        fo = open(xml_filename + '.new', "w")
        fo.write(''.encode('utf-8-sig'))

        for line in fi.readlines():
            newline = line.decode('utf-8')
            # <string name="msg_wifipwd_error">Wrong password</string>
            p = re.compile(u'<string name="([\w\-_]+)">(.*?)</string>')
            m = p.search(newline)
            if m:
                res_id = m.group(1)
                word = m.group(2)
                if contains_zh(word):
                    if self.reswords.has_key(res_id) and self.reswords[res_id].words[0] != "":
                        newline = newline.replace(word, self.reswords[res_id].words[0])                        
                    else:
                        if self.reverse_map.has_key(word):
                            newline = newline.replace(word, self.reverse_map[word])
                    
            fo.write(newline.encode('utf-8'))

        fi.close()
        fo.close()
        return True


def print_usage():
    this_name = os.path.split(sys.argv[0])[1]
    print "Usage example:"
    print "python %s -l d:\\a.csv -d d:\\test -x d:\\a.xml -c d:\\b.csv -a d:\\d.xml -s" % (this_name)
    print "or"
    print "python %s --load d:\\a.csv --dir d:\\test --xml d:\\a.xml --csv d:\\b.csv --apply d:\\d.xml --supplement" % (
        this_name)


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hsd:x:c:l:a:",
                                   ["help", "supplement", "dir=", "xml=", "csv=", "load=", "apply="])
    except getopt.GetoptError, err:
        print str(err)
        print_usage()
        sys.exit(2)

    dirs = []
    xmls = []
    csv = ''
    load_csvs = []
    apply_xmls = []
    supplement = False
    for o, a in opts:
        if o in ("-h", "--help"):
            print_usage()
            sys.exit()
        elif o in ("-d", "--dir"):
            dirs.append(a)
        elif o in ("-x", "--xml"):
            xmls.append(a)
        elif o in ("-c", "--csv"):
            csv = a
        elif o in ("-l", "--load"):
            load_csvs.append(a)
        elif o in ("-a", "--apply"):
            apply_xmls.append(a)
        elif o in ("-s", "--supplement"):
            supplement = True
        else:
            assert False, "unhandled option"
            sys.exit(2)

    rm = res_manager()

    if len(load_csvs) > 0:
        for c in load_csvs:
            rm.read_csv(c)

    for d in dirs:
        rm.read_dir(d)

    for x in xmls:
        rm.read_xml(x)

    rm.reverse_supplement()

    if supplement:
        rm.supplement()

    if csv != '':
        rm.write_csv(csv)

    if len(apply_xmls) > 0:
        for a in apply_xmls:
            rm.apply_to_xml(a)


if __name__ == "__main__":
    main()