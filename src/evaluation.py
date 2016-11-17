import sys,os
import ast
import json
import re
import copy
from subprocess import Popen, PIPE

class Evaluation(object):
    """
    Get the evaluation of a corpus for a result.
    When constructing, pass the path of the corpus and the path of the result file. 
    For example, "../wt2g/" "../wt2g/results/idf1"
    """
    def __init__(self, collection_path):
        self.corpus_path = os.path.abspath(collection_path)
        if not os.path.exists(self.corpus_path):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print '[Evaluation Constructor]:Please provide a valid corpus path'
            exit(1)

        self.merged_results_root = os.path.join(self.corpus_path, 'merged_results')
        self.evaluation_results_root = os.path.join(self.corpus_path, 'evals')
        if not os.path.exists(self.evaluation_results_root):
            os.makedirs(self.evaluation_results_root)
        self.qrel_path = os.path.join(self.corpus_path, 'judgement_file')


    def gen_eval_results_paras(self, qrel_program_str):
        all_paras = []
        for fn in os.listdir(self.merged_results_root):
            if not os.path.exists( os.path.join(self.evaluation_results_root, fn) ):
                all_paras.append( (self.corpus_path, qrel_program_str, os.path.join(self.merged_results_root, fn), os.path.join(self.evaluation_results_root, fn)) )
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


    def get_all_performance_of_some_queries(self, qids):
        """
        get all kinds of performance

        @Input:
            qids (list) : a list contains the qid that to be returned

        @Return: a dict of all performances of qids
        """

        all_performances = self.get_all_performance()
        return {k: all_performances.get(k, None) for k in qids}

class EvaluationClueWeb2009(Evaluation):
    pass

class EvaluationClueWeb(Evaluation):
    # other than TREC Web Track 2009 since it uses "Expected MAP" as the major evaluation.
    def output_all_evaluations(self, qrel_program, result_file_path, eval_file_path):
        """
        get all kinds of performance

        @Return: a dict of all performances 

        Format:

        runid,topic,ndcg@20,err@20
        indri,51,0.37535,0.48743
        indri,52,0.05270,0.03263
        ...
        ...
        indri,amean,0.12321,0.08195

        """
        all_performances = {}
        program = copy.deepcopy(qrel_program)
        program.append( self.qrel_path )
        program.append( result_file_path )
        process = Popen(program, stdout=PIPE)
        stdout, stderr = process.communicate()
        idx = 0
        for line in stdout.split('\n'):
            idx += 1
            if idx == 1: # skip first line
                continue
            line = line.strip()
            if line:
                row = line.split(',')
                runid = row[0]
                qid = row[1] if row[1] != 'amean' else 'all'
                ndcg_20 = ast.literal_eval(row[2])
                err_20 = ast.literal_eval(row[3])
                if qid not in all_performances:
                    all_performances[qid] = {}
                all_performances[qid]['ndcg_cut_20'] = ndcg_20
                all_performances[qid]['err_cut_20'] = err_20

        with open( eval_file_path, 'wb' ) as o:
            json.dump(all_performances, o, indent=2)

class EvaluationMQ(Evaluation):
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
        qid = None
        for line in stdout.split('\n'):
            line = line.strip()
            if line:
                m1 = re.search(r'topic=(\d+)', line)
                if m1:
                    qid = m1.group(1)
                    continue
                m2 = re.search(r'AP=(.*?)\s+', line)
                if m2:
                    try:
                        ap = ast.literal_eval(m2.group(1))
                    except:
                        ap = 0.0
                    if qid not in all_performances:
                        all_performances[qid] = {}
                    all_performances[qid]['map'] = ap
                m3 = re.search(r'statMAP_on_valid_topics=(.*?)\s+', line)
                if m3:
                    try:
                        ap = ast.literal_eval(m3.group(1))
                    except:
                        ap = 0.0
                    if qid not in all_performances:
                        all_performances[qid] = {}
                    all_performances[qid]['map'] = ap

        with open( eval_file_path, 'wb' ) as o:
            json.dump(all_performances, o, indent=2)

if __name__ == '__main__':
    e = Evaluation('../../wt2g', '../../wt2g/results/tf1')
    print e.get_all_performance()

