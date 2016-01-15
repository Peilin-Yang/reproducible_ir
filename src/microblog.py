# -*- coding: utf-8 -*-
import sys,os
import json
import re
import csv
import ast
from datetime import datetime, timedelta
from dateutil import parser
import pytz
from dateutil.relativedelta import *
import itertools
from operator import itemgetter
from subprocess import Popen, PIPE
from inspect import currentframe, getframeinfo
import argparse
import numpy as np

reload(sys)
sys.setdefaultencoding('utf-8')


def exponetial(x, _lambda=0.1):
    return np.exp((-1)*x*_lambda)

def log_normal(diff, _mu=1.0, _lambda=1):
    x = np.divide(np.add(np.log(diff), -_mu), _lambda)
    _sum = np.copy(x)
    _values = np.copy(x)
    for i in range(1, 100):
        _values = _values*x*x/(2*i+1)
        _sum += _values
    phi = 0.5+(_sum/math.sqrt(2*math.pi))*np.exp(x*x/(-2.0))
    return 1 - phi

def log_logistic(diff, _mu=1.0, _lambda=1):
    A = np.exp(_mu/_lambda)
    return A/(A+np.power(diff, 1.0/_lambda))

def linear_cal(x):
    if x <=0:
        return 0
    return x

def linear(diff, _slope=-1.0, _intercept=0.5):
    A = diff*_slope+_intercept
    vfunc = np.vectorize(linear_cal)
    return vfunc(A)

class MicroBlog(object):
    """
    MicroBlog Related
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
        self.raw_corpus_root = os.path.join(self.corpus_path, 'raw_corpus')
        self.decay_results_root = os.path.join(self.corpus_path, 'decay_results')

    def gen_run_split_decay_paras(self, methods):
        all_paras = []
        if not os.path.exists(self.decay_results_root):
            os.makedirs(self.decay_results_root)
        with open( self.parsed_query_file_path ) as f:
            j = json.load(f)
            for ele in j:
                qid = ele['num']
                for m in methods:
                    if 'paras' in m:
                        for p in itertools.product(*[ele[1] for ele in m['paras'].items()]):
                            para_str = m['name']
                            tmp = '-method:%s' % m['name']
                            for k_idx, k in enumerate(m['paras'].keys()):
                                para_str += ',%s:%s' % (k, p[k_idx])
                                tmp += ',%s:%s' % (k, p[k_idx])
                            results_fn = os.path.join(self.decay_results_root, 'query_'+qid[2:]+tmp)
                            if not os.path.exists(results_fn):
                                all_paras.append( (self.corpus_path, qid, para_str, results_fn) )
                    else:
                        para_str = m['name']
                        results_fn = os.path.join(self.decay_results_root, 'query_'+qid[2:]+'-method:%s' % m['name'])
                        if not os.path.exists(results_fn):
                            all_paras.append( (self.corpus_path, qid, para_str, results_fn) )
        return all_paras

    def cal_diffs(self, qid, corpus_path, use_days=True):
        query_time = ''
        diffs = []
        with open(self.parsed_query_file_path) as f:
            j = json.load(f)
            for ele in j:
                if ele['num'] == qid:
                    # try:
                    #     querytime = datetime.strptime(ele['querytime'], '%a %b %d %H:%M:%S %z %Y')
                    # except:
                    #     querytime = datetime.strptime(ele['querytime'], '%a %b %d %H:%M:%S %Z %Y')
                    querytime = parser.parse(ele['querytime'])
                    #print querytime
                    break
        with open(corpus_path) as f:
            j = json.load(f)
            for doc in j:
                doctime = datetime.fromtimestamp(float(doc['epoch']), pytz.utc)
                diff = (querytime-doctime).days if use_days else querytime-doctime
                diffs.append([doc['id'], diff])
        return diffs

    def output_results(self):
        pass

    def cal_the_decay_results(self, qid, method_n_para, output_fn):
        #print self.raw_corpus_root, qid
        corpus_path = os.path.join(self.raw_corpus_root, qid)
        diffs = self.cal_diffs(qid, corpus_path)
        #print diffs
        diffs_array = np.asarray([ele[1] for ele in diffs])
        method = method_n_para.split(',')[0]
        paras = {ele.split(':')[0]:float(ele.split(':')[1]) for ele in method_n_para.split(',')[1:]}
        print method, paras
        if method == 'linear':
            scores = linear(diffs_array, paras['slope'], paras['intercept'])
        if method == 'exponetial':
            scores = exponetial(diffs_array, paras['lambda'])
        if method == 'lognormal':
            scores = log_normal(diffs_array, paras['mu'], paras['sigma'])
        if method == 'loglogistic':
            scores = log_logistic(diffs_array, paras['mu'], paras['sigma'])
        print scores
        raw_input()
        res = [(diffs[i][0], scores[i]) for i in range(len(diffs))]
        res.sort(key=itemgetter(1), reverse=True)
        print res


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-mb_decay", "--cal_the_decay_results",
        nargs=1,
        help="input: function_name and paras")

    args = parser.parse_args()

    if args.cal_the_decay_results:
        MicroBlog(args.cal_the_decay_results[0]).cal_the_decay_results()

        