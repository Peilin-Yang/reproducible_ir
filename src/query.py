# -*- coding: utf-8 -*-
import sys,os
import json
import re
import string
import ast
import xml.etree.ElementTree as ET
import uuid
import itertools
from subprocess import Popen, PIPE
from inspect import currentframe, getframeinfo
import argparse

reload(sys)
sys.setdefaultencoding('utf-8')


stopwords="a,about,above,after,again,against,all,am,an,and,any,are,aren't,as,\
at,be,because,been,before,being,below,between,both,but,by,can't,cannot,could,\
couldn't,did,didn't,do,does,doesn't,doing,don't,down,during,each,few,for,from,\
further,had,hadn't,has,hasn't,have,haven't,having,he,he'd,he'll,he's,her,here,\
here's,hers,herself,him,himself,his,how,how's,i,i'd,i'll,i'm,i've,if,in,into,\
is,isn't,it,it's,its,itself,let's,me,more,most,mustn't,my,myself,no,nor,not,of,\
off,on,once,only,or,other,ought,our,ours,ourselves,out,over,own,same,shan't,\
she,she'd,she'll,she's,should,shouldn't,so,some,such,than,that,that's,the,\
their,theirs,them,themselves,then,there,there's,these,they,they'd,they'll,\
they're,they've,this,those,through,to,too,under,until,up,very,was,wasn't,\
we,we'd,we'll,we're,we've,were,weren't,what,what's,when,when's,where,where's,\
which,while,who,who's,whom,why,why's,with,won't,would,wouldn't,you,you'd,\
you'll,you're,you've,your,yours,yourself,yourselves"
punct="""
'!"#$%&()*+,-./:;<=>?@[\]^_`{|}~'
"""

class Query(object):
    """
    Get the judgments of a corpus.
    When constructing, pass the path of the corpus. For example, "../wt2g/"
    """
    def __init__(self, collection_path):
        self.corpus_path = os.path.abspath(collection_path)
        if not os.path.exists(self.corpus_path):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print '[Evaluation Constructor]:Please provide a valid corpus path'
            exit(1)

        self.query_file_path = os.path.join(self.corpus_path, 'raw_topics')
        if not os.path.exists(self.query_file_path):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print """No query file found! 
                query file should be called "raw_topics" under 
                corpus path. You can create a symlink for it"""
            exit(1)

        self.parsed_query_file_path = os.path.join(self.corpus_path, 'parsed_topics.json')
        self.split_queries_root = os.path.join(self.corpus_path, 'split_queries')
        self.split_results_root = os.path.join(self.corpus_path, 'split_results')

    def write_query_file(self, t=[]):
        fpath = str(uuid.uuid4())
        with open(fpath, 'w') as f:
            for ele in t:
                f.write('<DOC>\n')
                f.write('<TEXT>\n')
                f.write(ele)
                f.write('\n')
                f.write('</TEXT>\n')
                f.write('</DOC>\n')
        return fpath


    def parse_query(self, t=[]):
        """
        use IndriTextTransformer to parse the query
        """
        fpath = self.write_query_file(t)
        try:
            process = Popen(['IndriTextTransformer', '-class=trectext', '-file='+fpath], stdout=PIPE)
            stdout, stderr = process.communicate()
            r = []
            for line in stdout.split('\n'):
                line = line.strip()
                if line:
                    r.append(line)
            os.remove(fpath)
        except:
            os.remove(fpath)
            raise NameError("parse query error!")
        return r


    def get_queries(self):
        """
        Get the query of a corpus

        @Return: a list of dict [{'num':'401', 'title':'the query terms',
         'desc':description, 'narr': narrative description}, ...]
        """

        if not os.path.exists(self.parsed_query_file_path):
            with open(self.query_file_path) as f:
                s = f.read()
                all_topics = re.findall(r'<top>.*?<\/top>', s, re.DOTALL)
                #print all_topics
                #print len(all_topics)

                _all = []
                for t in all_topics:
                    t = re.sub(r'<\/.*?>', r'', t, flags=re.DOTALL)
                    a = re.split(r'(<.*?>)', t.replace('<top>',''), re.DOTALL)
                    #print a
                    aa = [ele.strip() for ele in a if ele.strip()]
                    #print aa
                    d = {}
                    for i in range(0, len(aa), 2):
                        """
                        if i%2 != 0:
                            if aa[i-1] == '<num>':
                                aa[i] = aa[i].split()[1]
                            d[aa[i-1][1:-1]] = aa[i].strip().replace('\n', ' ')
                        """
                        tag = aa[i][1:-1]
                        value = aa[i+1].replace('\n', ' ').strip().split(':')[-1].strip()
                        if tag != 'num' and value:
                            value = self.parse_query([value])[0]

                        d[tag] = value
                    _all.append(d)

            with open(self.parsed_query_file_path, 'wb') as f:
                json.dump(_all, f, indent=2)

        with open(self.parsed_query_file_path) as f:
            return json.load(f)

    def get_queries_dict(self):
        """
        Get the query of a corpus

        @Return: a dict with keys as qids {'401':{'title':'the title', 'desc':'the desc'}, ...}
        """
        all_queries = self.get_queries()
        all_queries_dict = {}
        for ele in all_queries:
            qid = ele['num']
            all_queries_dict[qid] = ele

        return all_queries_dict
        
    def get_queries_of_length(self, length):
        """
        Get the queries of a specific length

        @Input:
            length - the specific length. For example, length=1 get all queries
                     with single term

        @Return: a list of dict [{'num':'403', 'title':'osteoporosis',
         'desc':description, 'narr': narrative description}, ...]
        """

        all_queries = self.get_queries()
        filtered_queries = [ele for ele in all_queries if len(ele['title'].split()) == length]

        return filtered_queries


    def indent(self, elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i


    def gen_query_file_for_indri(self, output_foler='split_queries', 
            index_path='index', is_trec_format=True, count=1000, use_which_part=['title']):
        """
        generate the query file for Indri use.

        @Input:
            output_root - the output root of the splitted query files
            index_path - the index path, default "index".
            is_trec_format - whether to output the results in TREC format, default True
            count - how many documents will be returned for each topic, default 1000
        """
        output_root = os.path.join(self.corpus_path, output_foler)
        if not os.path.exists(output_root):
            os.makedirs(output_root)

        all_topics = self.get_queries()

        for ele in all_topics:
            for part in use_which_part:
                qf = ET.Element('parameters')
                index = ET.SubElement(qf, 'index')
                index.text = os.path.join(self.corpus_path, index_path)
                ele_trec_format = ET.SubElement(qf, 'trecFormat')
                ele_trec_format.text = 'true' if is_trec_format else 'false'
                ele_count = ET.SubElement(qf, 'count')
                ele_count.text = str(count)
                
                t = ET.SubElement(qf, 'query')
                qid = ET.SubElement(t, 'number')
                qid.text = str(int(ele['num']))
                q = ET.SubElement(t, 'text')
                q.text = ''
                for sep_part in part.split('+'):
                    q.text += ele[sep_part]+' '

                self.indent(qf)

                tree = ET.ElementTree(qf)
                tree.write(os.path.join(self.corpus_path, output_root, part+'_'+qid.text))


    def gen_run_split_query_paras(self, methods, use_which_part=['title']):
        all_paras = []
        if not os.path.exists(self.split_results_root):
            os.makedirs(self.split_results_root)

        for qf in os.listdir( self.split_queries_root ):
            which_part = qf.split('_')[0]
            if which_part not in use_which_part:
                continue
            for m in methods:
                if 'paras' in m:
                    for p in itertools.product(*[ele[1] for ele in m['paras'].items()]):
                        para_str = '-rule=method:%s' % m['name']
                        tmp = '-method:%s' % m['name']
                        for k_idx, k in enumerate(m['paras'].keys()):
                            para_str += ',%s:%s' % (k, p[k_idx])
                            tmp += ',%s:%s' % (k, p[k_idx])
                        if m['name'] == 'worddocdensity':
                            para_str += ',dd_score_folder:%s' % os.path.join(self.corpus_path, 'queries_dd')
                        results_fn = os.path.join(self.split_results_root, qf+tmp)
                        if not os.path.exists(results_fn):
                            all_paras.append( (os.path.join(self.split_queries_root, qf), \
                                para_str, results_fn) )
                else:
                    para_str = '-rule=method:%s' % m['name']
                    results_fn = os.path.join(self.split_results_root, qf+'-method:%s' % m['name'])
                    if m['name'] == 'smart':
                            para_str += ',ctf_score_folder:%s' % os.path.join(self.corpus_path, 'smart_ctf')
                    if not os.path.exists(results_fn):
                        all_paras.append( (os.path.join(self.split_queries_root, qf), \
                            para_str, results_fn) )
        return all_paras


class ClueWebQuery(Query):
    def get_queries(self):
        """
        Get the query of a corpus

        @Return: a list of dict [{'num':'401', 'title':'the query terms',
         'desc':description, 'narr': narrative description}, ...]
        """

        if not os.path.exists(self.parsed_query_file_path):
            _all = []
            with open(self.query_file_path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        row = line.split(':')
                        num = row[0]
                        text = row[1]
                        query_text = self.parse_query([text])[0]
                        _all.append({'num':num, 'title':query_text})

            with open(self.parsed_query_file_path, 'wb') as f:
                json.dump(_all, f, indent=2)

        with open(self.parsed_query_file_path) as f:
            return json.load(f)    



if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-1", "--gen_standard_queries",
        nargs=1,
        help="Generate the standard queries for Indri. Please give the collection path!")

    args = parser.parse_args()

    if args.gen_standard_queries:
        Query(args.gen_standard_queries[0]).gen_query_file_for_indri()

