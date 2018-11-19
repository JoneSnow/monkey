# -*- coding: utf-8 -*-
'''
Project: python2
Filename: UnicodeWriter
Author: SEELE
Date: 2017/4/11- 22:26
'''
import cStringIO
import codecs
import csv


# 这个类来自官方文档
class UnicodeWriter(object):
    '''csv支持写入unicode'''
    def __init__(self, f, dialect=csv.excel, encoding="utf-8-sig", **kwds):
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        '''writerow(unicode) -> None
        This function takes a Unicode string and encodes it to the output.
        '''
        self.writer.writerow([s.encode("utf-8") for s in row])
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        data = self.encoder.encode(data)
        self.stream.write(data)
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """

    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")


class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    支持读取unicode CSV
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

if __name__ == "__main__":
    '''Test code'''
    name = u'BrownWong你好哈哈'
    with open(r'test.csv', 'wb') as infile:
        writer = UnicodeWriter(infile, delimiter=',')
        writer.writerow([name])

    with open(r'test.csv', 'rb') as fileCsv:
        fileCsv = UnicodeReader(fileCsv)
        for item in fileCsv:
            print(item)