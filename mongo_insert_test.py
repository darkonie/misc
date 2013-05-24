import string
import random
from multiprocessing import Process
from optparse import OptionParser

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

MONGO_USER = ''
MONGO_PASS = ''
MONGO_DB = 'testdb'
MONGO_COLLECTION = 'helloworld'
MONGO_HOST = 'localhost'
MONGO_PORT= 27017


'''
class MongoTest
Generates random documents and insert into mongodb for test

doc_size_k = the size of document in kb
db_limit_g = the limit of database in gb
so we will have db_limit_g / doc_size_k documents in total
'''
class MongoTest(Process):
    def __init__(self,
                 doc_size_k=18,
                 db_limit_g=4,
                 proc_num=1):

        Process.__init__(self)
        print 'Starting process %s' % self.name
        self.doc_size_k = doc_size_k * 1024 
        self.db_limit_k = db_limit_g * 1024 * 1024 * 1024 
        self.proc_num = proc_num

        if (MONGO_USER == '' or MONGO_PASS == ''):
            client = MongoClient(MONGO_HOST, MONGO_PORT)
        else:
            client = MongoClient('mongodb://%s:%s@%s:%d' % (MONGO_USER,
                                                            MONGO_PASS,
                                                            MONGO_HOST,
                                                            MONGO_PORT))
        db = client[MONGO_DB]
        self.collection = db[MONGO_COLLECTION]

    def generate_random_text(self, str_size):
        return ''.join(
                    random.choice(
                        string.ascii_uppercase + string.digits,
                    ) for x in range(str_size)
                )

    def generate_random_doc(self):
        shardkey = 1
        key_limit = [3,10] # key limit in a lenght range of random document key. e.g.    { 'ASSBAA': 'QWHJESDJDSDKSDJKD...document_size' }, ASSBAA is a key
        count_per_process = (self.db_limit_k / self.doc_size_k) / self.proc_num
        print 'I will insert %d documents with size of %d bytes\n\n' % (count_per_process,
                                                                        self.doc_size_k)
        for iteration in xrange(count_per_process):
            self.insert_into_mongo(self.generate_random_text(random.randint(key_limit[0],key_limit[1])),
                                   self.generate_random_text(self.doc_size_k), shardkey)
            shardkey = shardkey + 2

        print 'Process %s is done' % self.name

    def insert_into_mongo(self, key, value, shardkey):
        try:
            self.collection.insert({key: value, 'script': 'v2', 'aliasnum': '%d' % shardkey})
        except DuplicateKeyError:
            shardkey = shardkey + 1
            self.insert_into_mongo(key, value, shardkey)

    def run(self):
        self.generate_random_doc()
        return


if __name__ == '__main__':
    parser = OptionParser('\n'.join((
        'Usage: %prog -s <size of document kb> -l <limit of database gb>',
        'example:',
        '\t%prog -s 16 -l 5'
    )))
    parser.add_option("-s", "--size", dest="docsize",
                  help="Document size in KB", type="int")
    parser.add_option("-l", "--limit", dest="dblimit",
                  help="Database size limit in GB", type="int")
    parser.add_option("-p", "--processes", dest="proc_num",
                  help="number of processes running in concurency, default = 1", type="int", default="1")
    options, params = parser.parse_args()

    if (parser.values.docsize == None or parser.values.dblimit == None):
        parser.print_usage()
    else:
    	for process_id in range(parser.values.proc_num):
    	    process = MongoTest(parser.values.docsize, parser.values.dblimit, parser.values.proc_num)
    	    process.start()
