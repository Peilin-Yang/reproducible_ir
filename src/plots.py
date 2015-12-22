# -*- coding: utf-8 -*-
import os,sys
import numpy as np
import argparse
import csv
from inspect import currentframe, getframeinfo
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

reload(sys)
sys.setdefaultencoding('utf-8')

class Plots(object):
    """
    Plot the results.
    When constructing, pass the path of the corpus. For example, "../wt2g/"
    """
    def __init__(self, collection_paths):
        # we can plot multiple collections on one canvas
        self.collection_paths = collection_paths

    def check_valid_path(self, collection_path):
        self.corpus_path = os.path.abspath(collection_path)
        if not os.path.exists(self.corpus_path):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print '[Plots]:collection path ' + collection_path + ' does not exist....'
            exit(1)

        self.performance_root = os.path.join(self.corpus_path, 'performances')
        if not os.path.exists(self.performance_root):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print '[Plots]:performance path ' + self.performance_root + ' does not exist....'
            exit(1)

    def load_optimal_performance(self, evaluation_method='map', query_part='title'):
        data = []
        with open('g.json') as f:
            j = json.load(f)
            for m in j['methods']:
                if not 'formal_name' in m:
                    continue
                with open(os.path.join(self.performance_root, query_part+'-'+m['name'])) as pf:
                    all_performance = json.load(pf)
                    required = all_performance[evaluation_method]
                    data.append( (m['name'], m['formal_name'], m['year'], 
                        required['max']['value'], required['max']['para']) )
        data.sort(key=itemgetter(2))
        return data
 
    def plot_optimal_for_single_collection(self, collection_path, ax=None, 
            evaluation_method='map', query_part='title'):
        self.check_valid_path(collection_path)
        data = self.load_optimal_performance(evaluation_method, query_part)

        markers = ['.', '+', 'v', 'o', 's', 'x', '1', '8', 'p', '*', 'h', 'H', 
            'D', 'd', '2', '3', '4']
        marker_idx = 0
        for d in data:
            #xaxis = np.arange(data[0][2]-1, data[-1][2]+1)
            #xticks = sorted([float(ele[7:]) for ele in self.data_splits_include])
            #yaxis = [data[evaluation_method][feature_label][data_split_label] for data_split_label in self.data_splits_include if feature_label in data[evaluation_method]]
            #print xaxis
            #print xticks
            #print yaxis
            #if len(xaxis) != len(yaxis):
                #continue
            ax.plot(d[2], d[3], markers[marker_idx], label=d[1])
            marker_idx += 1
            #print feature_label+':'+evaluation_method+':'+str(yaxis)
        ax.set_title(collection_path.split('/')[-1])
        ax.set_xlim([data[0][2]-1, data[-1][2]+1])
        #xticks.insert(0, '')
        #xticks.append('')
        #xticks(x+2*width, xticks, rotation=40)
        #print xaxis
        #ax.set_xticks(np.arange(1, len(self.data_splits_include)+1))
        ax.set_xticklabels(xticks, rotation=40)

    def plot_optimal_for_all_collections(self, 
            evaluation_method='map', query_part='title'):
        num_cols = 2
        num_rows = len(self.collection_paths)
        size = 3
        fig, axs = plt.subplots(nrows=num_rows, ncols=num_cols, sharex=True, 
            sharey=False, figsize=(size*num_cols, size*num_rows))
        font = {'size' : 16}
        plt.rc('font', **font)
        row_idx = 0
        col_idx = 0
        for collection in self.collection_paths:
            ax = axs[col_idx]
            self.plot_optimal_for_single_collection(collection, ax, 
                evaluation_method, query_part)
            col_idx += 1
            if col_idx >= num_cols:
                col_idx = 0
            
        plot_figures_root = '../plots/'        
        if not os.path.exists(plot_figures_root):
            os.makedirs(plot_figures_root)
        output_fn = os.path.join(plot_figures_root, evaluation_method+'-'+query_part+'.eps')
        plt.savefig(output_fn, format='eps', bbox_inches='tight', dpi=100)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-a", "--plot_optimal",
        nargs='+',
        help="plots the optimal performances for all collections")

    args = parser.parse_args()

    if args.plot_optimal:
        print args.plot_optimal
        Plots(collection_paths=args.plot_optimal).plot_optimal_for_all_collections()


