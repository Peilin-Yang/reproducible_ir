import os,sys
import csv
import ast
import json
from subprocess import Popen, PIPE


class CollectionStats():
    def __init__(self, path):
        self.collection_path = os.path.abspath(path)
        if not os.path.exists(self.collection_path):
            print '[CollectionStats Constructor]:Please provide a valid results file path'
            exit(1)


    def get_index_statistics(self):
        process = Popen(['dumpindex', os.path.join(self.collection_path, 'index'), 's'], stdout=PIPE)
        stdout, stderr = process.communicate()
        stats = {}
        for line in stdout.split('\n'):
            line = line.strip()
            if line:
                row = line.split(':')
                try:
                    stats[row[0].strip()] = ast.literal_eval(row[1].strip())
                except:
                    continue

        return stats        

    def get_avdl(self):
        all_statistics = self.get_index_statistics()
        return all_statistics.get('average doc length', None)

    def get_doc_counts(self):
        all_statistics = self.get_index_statistics()
        return all_statistics.get('documents', None)

    def re_gen_do_statistics_json(self):
        output_root = os.path.join(self.collection_path, 'docs_statistics_json')
        if not os.path.exists(output_root):
            os.makedirs(output_root)
        for fn in os.listdir(os.path.join(self.collection_path, 'multiply_to_be_best')):
            qid = fn.split('_')[1]
            output = os.path.join(output_root, qid)
            if not os.path.exists(output):
                print fn
                output_json = {}
                with open(os.path.join(self.collection_path, 'multiply_to_be_best', fn)) as f:
                    rows = csv.DictReader(f)
                    for row in rows:
                        output_json[row['docID']] = \
                            {'IDF':row['IDF'],\
                            'TF':row['TF'],\
                            'TOTAL_TF':int(row['TOTAL_TF']),\
                            'doc_length':int(row['doc_length'])}
                with open(output, 'wb') as f:
                    json.dump(output_json, f)


    def get_doc_statistics(self, qid, did):
        with open(os.path.join(self.collection_path, 'docs_statistics_json', qid)) as f:
            jf = json.load(f)
            return jf.get(did, None)

    def get_qid_doc_statistics(self, qid):
        with open(os.path.join(self.collection_path, 'docs_statistics_json', qid)) as f:
            return json.load(f)

    def get_idf(self, qid):
        with open(os.path.join(self.collection_path, 'multiply_to_be_best', 'idf1_'+qid)) as f:
            rows = csv.DictReader(f)
            for row in rows:
                return row['IDF']


    def get_term_stats(self, term, feature):
        """
        Get a statistics of a term

        @Input:
            term (string) : the term that whose statistics is needed
            feature (string) : the required feature

        @Return: the required statistics
        """

        process = Popen(['dumpindex', 
            os.path.join(self.collection_path, 'index'), 'sf', term, feature], 
            stdout=PIPE)
        stdout, stderr = process.communicate()

        return stdout

    def get_maxTF(self, term):
        r = self.get_term_stats(term, 'maxTF').strip()
        return int(r.split()[-1])

    def get_richStats(self):
        richStatsFilePath = os.path.join(self.collection_path, 'rich_stats.json')
        if not os.path.exists(richStatsFilePath):
            f = open(richStatsFilePath, 'wb')
            all_performances = {}
            process = Popen(['dumpindex', os.path.join(self.collection_path, 'index'), 'rs'], stdout=f)
            stdout, stderr = process.communicate()
            f.close()

        with open(richStatsFilePath) as f:
            return json.load(f)

    def get_term_counts(self, term):
        process = Popen(['dumpindex', 
            os.path.join(self.collection_path, 'index'), 't', term], 
            stdout=PIPE)
        stdout, stderr = process.communicate()

        all_term_counts = []
        for line in stdout.split('\n')[1:-2]:
            line = line.strip()
            if line:
                row = line.split()
                all_term_counts.append(row)

        return all_term_counts


if __name__ == '__main__':
    CollectionStats('../../wt2g/').re_gen_do_statistics_json()
    CollectionStats('../../trec8/').re_gen_do_statistics_json()
    CollectionStats('../../trec7/').re_gen_do_statistics_json()