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
import math
import numpy as np

import performance

reload(sys)
sys.setdefaultencoding('utf-8')


def exponential(x, _lambda=0.1):
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
        self.merged_rel_results_root = os.path.join(self.corpus_path, 'merged_results')
        self.merged_decay_results_root = os.path.join(self.corpus_path, 'merged_decay_results')
        if not os.path.exists(self.merged_decay_results_root):
            os.makedirs(self.merged_decay_results_root)
        self.combine_results_root = os.path.join(self.corpus_path, 'combined_results')
        self.merged_combine_results_root = os.path.join(self.corpus_path, 'merged_combined_results')
        if not os.path.exists(self.merged_combine_results_root):
            os.makedirs(self.merged_combine_results_root)
        self.eval_decay_root = os.path.join(self.corpus_path, 'evals_mb_decay')
        if not os.path.exists(self.eval_decay_root):
            os.makedirs(self.eval_decay_root)
        self.eval_combine_root = os.path.join(self.corpus_path, 'evals_mb_combine')
        if not os.path.exists(self.eval_combine_root):
            os.makedirs(self.eval_combine_root)
        self.qrel_path = os.path.join(self.corpus_path, 'judgement_file')

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

    def cal_diffs(self, qid, corpus_path):
        query_time = ''
        diffs = []
        docid_set = set()
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
                docid = doc['id']
                if docid in docid_set:
                    continue
                docid_set.add(docid)
                doctime = datetime.fromtimestamp(float(doc['epoch']), pytz.utc)
                diff = (querytime-doctime).total_seconds()
                diffs.append([docid, diff])
        return diffs

    def output_results(self, output_fn, qid, scores, runid):
        with open(output_fn, 'wb') as f:
            idx = 1
            for ele in scores:
                docid = ele[0]
                score = ele[1]
                f.write('%s Q0 %s %d %f %s\n' % (qid[2:], docid, idx, score, runid))
                idx += 1

    def cal_the_decay_results(self, qid, method_n_para, output_fn):
        #print self.raw_corpus_root, qid
        corpus_path = os.path.join(self.raw_corpus_root, qid)
        diffs = self.cal_diffs(qid, corpus_path)
        #print diffs
        diffs_array = np.asarray([ele[1] for ele in diffs])
        method = method_n_para.split(',')[0]
        if len(method_n_para.split(',')) > 1:
            paras = {ele.split(':')[0]:float(ele.split(':')[1]) for ele in method_n_para.split(',')[1:]}
        #print method, paras
        if method == 'linear':
            scores = linear(diffs_array, paras['slope'], paras['intercept'])
        if method == 'exponential':
            scores = exponential(diffs_array, paras['lambda'])
        if method == 'lognormal':
            scores = log_normal(diffs_array, paras['mu'], paras['sigma'])
        if method == 'loglogistic':
            scores = log_logistic(diffs_array, paras['mu'], paras['sigma'])
        #print scores
        res = [(diffs[i][0], scores[i]) for i in range(len(diffs))]
        res.sort(key=itemgetter(1), reverse=True)
        self.output_results(output_fn, qid, res, method_n_para)


    def output_combined_rel_decay_scores(self):
        funcs = {'rel': ['okapi','pivoted','f2exp'], 'decay':['exponential', 'lognormal', 'loglogistic']}
        p = performance.Performances(self.corpus_path)
        scores = {}
        for k,v in funcs.items():
            optimal_pfms = p.load_optimal_performance(v, 'map', 'query')
            if k == 'rel':
                paths = {ele[0]:os.path.join(self.merged_rel_results_root, 'query-method:'+ele[0]+','+ele[2]) for ele in optimal_pfms}
            if k == 'decay':
                paths = {ele[0]:os.path.join(self.merged_decay_results_root, 'query-method:'+ele[0]+','+ele[2]) for ele in optimal_pfms}
            for method, path in paths.items():
                scores[method] = {}
                with open(path) as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            row = line.split()
                            qid = row[0]
                            did = row[2]
                            score = row[4]
                            if qid not in scores[method]:
                                scores[method][qid] = {}
                            scores[method][qid][did] = score
                            print scores
                            raw_input()

    def gen_merge_decay_results_paras(self, total_query_cnt, use_which_part=['title']):
        all_paras = []
        all_results = {}
        for fn in os.listdir(self.decay_results_root):
            #print fn
            query = fn.split('-')[0]
            method = '-'.join(fn.split('-')[1:])
            query_part, qid = query.split('_')
            label = query_part+'-'+method
            collect_results_fn = os.path.join(self.merged_decay_results_root, label)
            if not os.path.exists(collect_results_fn):
                if label not in all_results:
                    all_results[label] = []
                all_results[label].append( os.path.join(self.decay_results_root, fn) )

        for label in all_results:
            if len(all_results[label]) < total_query_cnt:
                print 'Results of '+ self.corpus_path + ':' + label +' not enough (%d/%d).' % (len(all_results[label]), total_query_cnt)
                continue
            tmp = [os.path.join(self.merged_decay_results_root, label)]
            tmp.extend( all_results[label] )
            all_paras.append(tmp)

        return all_paras

    def gen_eval_results_paras(self, qrel_program_str):
        all_paras = []
        folders = [self.merged_decay_results_root, self.merged_combine_results_root]
        for folder in folders:
            if os.path.exists(folder):
                eval_root = self.eval_decay_root if folder == self.merged_decay_results_root else self.eval_combine_root
                for fn in os.listdir(folder):
                    if not os.path.exists( os.path.join(eval_root, fn) ):
                        all_paras.append( (self.corpus_path, qrel_program_str, os.path.join(folder, fn), os.path.join(eval_root, fn)) )
        return all_paras

    def output_all_evaluations(self, qrel_program, result_file_path, eval_file_path):
        """
        get all kinds of performance

        @Return: a dict of all performances 
        """
        all_performances = {}
        program = copy.deepcopy(qrel_program)
        program.append( self.qrel_path )
        program.append( result_file_path )
        process = Popen(program, stdout=PIPE)
        stdout, stderr = process.communicate()
        for line in stdout.split('\n'):
            line = line.strip()
            if line:
                row = line.split()
                evaluation_method = row[0]
                qid = row[1]
                try:
                    performace = ast.literal_eval(row[2])
                except:
                    continue

                if qid not in all_performances:
                    all_performances[qid] = {}
                all_performances[qid][evaluation_method] = performace

        with open( eval_file_path, 'wb' ) as o:
            json.dump(all_performances, o, indent=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-mb_decay", "--cal_the_decay_results",
        nargs=1,
        help="input: function_name and paras")

    args = parser.parse_args()

    if args.cal_the_decay_results:
        MicroBlog(args.cal_the_decay_results[0]).cal_the_decay_results()

        