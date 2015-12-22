# -*- coding: utf-8 -*-
import os,sys
import numpy as np
import argparse
import csv
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

        self.performance_root = os.path.join(self.corpus_path, 'performance')
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
        data = self.load_optimal_performance(evaluation_methodm, query_part)



    def plot_optimal_for_all_collections(self):
        num_cols = 2
        num_rows = len(self.collection_paths)
        size = 3
        fig, axs = plt.subplots(nrows=num_rows, ncols=num_cols, sharex=True, 
            sharey=False, figsize=(size*num_cols, size*num_rows))
        font = {'size' : 16}
        plt.rc('font', **font)
        row_idx = 0
        col_idx = 0

        markers = ['.', '+', 'v', 'o', 's', 'x']
        #colors = ['red', 'blue', 'green', 'cyan']
        #patterns = ('-', '+', 'x', '\\')
        width = 0.35
        #changeable_para_labels = [ele for ele in para_labels if ele not in fixed_paras]
        for evaluation_method in data:
            ax = axs[col_idx]
            marker_idx = 0
            for feature_label in feature_list:
                xaxis = np.arange(1, len(self.data_splits_include)+1)
                xticks = sorted([float(ele[7:]) for ele in self.data_splits_include])
                yaxis = [data[evaluation_method][feature_label][data_split_label] for data_split_label in self.data_splits_include if feature_label in data[evaluation_method]]
                print xaxis
                print xticks
                print yaxis
                if len(xaxis) != len(yaxis):
                    continue
                ax.plot(xaxis, yaxis, markers[marker_idx]+'-', label=feature_label)
                marker_idx += 1
                #print feature_label+':'+evaluation_method+':'+str(yaxis)
            ax.set_title(evaluation_method)
            ax.set_xlim([0, len(self.data_splits_include)+1])
            #xticks.insert(0, '')
            #xticks.append('')
            #xticks(x+2*width, xticks, rotation=40)
            #print xaxis
            ax.set_xticks(np.arange(1, len(self.data_splits_include)+1))
            ax.set_xticklabels(xticks, rotation=40)
            
            col_idx += 1
            if col_idx >= 2:
                ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
                col_idx = 0
            
        plot_figures_root = '../less_data_plots/'        
        if not os.path.exists(plot_figures_root):
            os.makedirs(plot_figures_root)
        output_fn = os.path.join(plot_figures_root, plot_label+'-'+self.collection+'.eps')
        plt.savefig(output_fn, format='eps', bbox_inches='tight', dpi=100)


    def plot_less_data_all_collections(self, optimal_data, plot_label, \
            include_suboptimal_results=False, suboptimal_data=None, \
            include_ltr_results=False, ltr_data=None):
        #feature_list = ['CAT', 'DES', 'FR', 'SR', 'NR', 'RS']
        feature_list = ['CAT', 'DES', 'NR']
        collection_mapping = {'trec2012_cs': 'CS2012', 'trec2013_cs': 'CS2013', 'trec2014_cs':'CS2014', 'yelp': 'Yelp'}
        #print data
        num_cols = 2
        num_rows = len(collections)
        size = 3
        fig, axs = plt.subplots(nrows=num_rows, ncols=num_cols, sharex=True, sharey=False, figsize=(size*num_cols, size*num_rows))
        font = {'size' : 10}
        plt.rc('font', **font)
        row_idx = 0
        col_idx = 0

        legend_line_list = []
        legend_line_list_has = False
        for c in collections:
            markers = ['.', '+', 'v', '*', 'x']
            col_idx = 0
            for evaluation_method in optimal_data[c]:
                ax = axs[row_idx][col_idx]
                marker_idx = 0
                for feature_label in feature_list:
                    xaxis = np.arange(1, len(self.data_splits_include)+1)
                    xticks = sorted([int(ele[-1]+'0') for ele in self.data_splits_include])
                    yaxis = [optimal_data[c][evaluation_method][feature_label][data_split_label] for data_split_label in self.data_splits_include if feature_label in optimal_data[c][evaluation_method]]
                    #print xaxis
                    #print xticks
                    if len(yaxis) == 0:
                        yaxis = [0] * len(xaxis)
                    if len(xaxis) != len(yaxis):
                        print yaxis, 'continue'
                        continue
                    l, = ax.plot(xaxis, yaxis, markers[marker_idx]+'-')
                    if not legend_line_list_has:
                        legend_line_list.append(l)
                    if include_suboptimal_results and feature_label != 'CAT' and feature_label != 'DES':
                        yaxis = [suboptimal_data[c][evaluation_method][feature_label][data_split_label] for data_split_label in self.data_splits_include if feature_label in suboptimal_data[c][evaluation_method]]
                        if len(yaxis) == 0:
                            yaxis = [0] * len(xaxis)
                        if len(xaxis) != len(yaxis):
                            continue
                        #print yaxis
                        marker_idx += 1
                        l, = ax.plot(xaxis, yaxis, markers[marker_idx]+'-')
                        if not legend_line_list_has:
                            legend_line_list.append(l)
                    if include_ltr_results and feature_label != 'CAT' and feature_label != 'DES':
                        #print c, evaluation_method, feature_label
                        yaxis = [ltr_data[c][evaluation_method][feature_label][data_split_label] for data_split_label in self.data_splits_include if feature_label in ltr_data[c][evaluation_method]]
                        if len(yaxis) == 0:
                            yaxis = [0] * len(xaxis)
                        if len(xaxis) != len(yaxis):
                            continue
                        #print yaxis
                        marker_idx += 1
                        l, = ax.plot(xaxis, yaxis, markers[marker_idx]+'-')
                        if not legend_line_list_has:
                            legend_line_list.append(l)
                    marker_idx += 1
                    #print feature_label+':'+evaluation_method+':'+str(yaxis)
                if not legend_line_list_has:
                    ax.set_title(r'$%s$' % evaluation_method)
                ax.set_xlim([0, len(self.data_splits_include)+1])
                if col_idx == 0:
                    ax.set_ylabel(r'$%s$' % collection_mapping[c], size=16)
                ax.set_xticks(np.arange(1, len(self.data_splits_include)+1))
                #ax.set_xticklabels(xticks, rotation=40)
                ax.set_xticklabels(xticks, rotation=40)
                if row_idx == num_rows-1:
                    ax.set_xlabel(r'$p$', size=16)
                    if col_idx == 0:
                        ax.set_ylim([0.6, 0.9])
                    if col_idx == 1:
                        ax.set_ylim([0.6, 1.0])
                
                col_idx += 1
            legend_line_list_has = True
            row_idx += 1
                
        if include_suboptimal_results:
            legend_list = ['CAT', 'DES']
            for f in feature_list: 
                if f != 'CAT' and f != 'DES':
                    legend_list.append(f+'(optimal)')
                    legend_list.append(f+'(sub-optimal)')
        else:
            legend_list = feature_list
            legend_list[-1] = 'NR(LI)'

        if include_ltr_results:
            legend_list.append('NR(LTR)')
        print legend_list
        fig.legend(tuple(legend_line_list), legend_list, ncol=4, loc=8, fontsize=12) # lower center
        #fig.tight_layout()

        plot_figures_root = '../less_data_plots/'        
        if not os.path.exists(plot_figures_root):
            os.makedirs(plot_figures_root)
        output_fn = os.path.join(plot_figures_root, plot_label+'.eps')
        plt.savefig(output_fn, format='eps', bbox_inches='tight', dpi=100)


    def load_optimal_data(self):
        performance_fn = os.path.join(self.rel_collection_path, 'all_final_performances.csv')
        allowed_methods = ['interpolation']
        #collection_mapping = {'trec2012_cs': 'CS2012', 'trec2013_cs': 'CS2013', 'trec2014_cs':'CS2014'}
        feature_label_mapping = {'category': 'CAT', 'description': 'DES', 'fr': 'FR', 'usr':'SR', 'nr':'NR', 'rs':'RS'}
        data = {}

        with open(performance_fn) as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                suggestion_split_label = row['suggestion_splits']
                validation_label = row['testing_strategy']
                feature_label = row['feature']
                method_label = row['method']
                try:
                    err20 = float(row['ERR@20'])
                except:
                    continue
                try:
                    p5 = float(row['P@5'])
                except:
                    continue

                if method_label not in allowed_methods:
                    continue
                if 'AllUser' in suggestion_split_label:
                    continue
                if 'without_validation' in validation_label:
                    continue
                if feature_label not in feature_label_mapping:
                    continue

                feature_label = feature_label_mapping[feature_label]

                if 'ERR@20' not in data:
                    data['ERR@20'] = {}
                if feature_label not in data['ERR@20']:
                    data['ERR@20'][feature_label] = {}
                data['ERR@20'][feature_label][suggestion_split_label] = err20
                if 'P@5' not in data:
                    data['P@5'] = {}
                if feature_label not in data['P@5']:
                    data['P@5'][feature_label] = {}
                data['P@5'][feature_label][suggestion_split_label] = p5
        return data

    def load_suboptimal_data(self):
        performance_fn = os.path.join(self.rel_collection_path, 'suboptimal_performance', 'interpolation.csv')
        #collection_mapping = {'trec2012_cs': 'CS2012', 'trec2013_cs': 'CS2013', 'trec2014_cs':'CS2014'}
        feature_label_mapping = {'category': 'CAT', 'description': 'DES', 'fr': 'FR', 'usr':'SR', 'nr':'NR', 'rs':'RS'}
        data = self.load_optimal_data()

        with open(performance_fn) as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                suggestion_split_label = row['suggestion_splits']
                validation_label = row['testing_strategy']
                feature_label = row['feature']
                err20 = row['ERR@20']
                p5 = row['P@5']
                try:
                    err20 = float(row['ERR@20'])
                except:
                    continue
                try:
                    p5 = float(row['P@5'])
                except:
                    continue

                if 'AllUser' in suggestion_split_label:
                    continue
                if 'without_validation' in validation_label:
                    continue
                if feature_label not in feature_label_mapping:
                    continue

                feature_label = feature_label_mapping[feature_label]

                if 'ERR@20' not in data:
                    data['ERR@20'] = {}
                if feature_label not in data['ERR@20']:
                    data['ERR@20'][feature_label] = {}
                data['ERR@20'][feature_label][suggestion_split_label] = err20
                if 'P@5' not in data:
                    data['P@5'] = {}
                if feature_label not in data['P@5']:
                    data['P@5'][feature_label] = {}
                data['P@5'][feature_label][suggestion_split_label] = p5
                    
        return data

    def load_ltr_data(self):
        performance_fn = os.path.join(self.rel_collection_path, 'all_final_performances.csv')
        allowed_methods = ['MART']
        #collection_mapping = {'trec2012_cs': 'CS2012', 'trec2013_cs': 'CS2013', 'trec2014_cs':'CS2014'}
        feature_label_mapping = {'category': 'CAT', 'description': 'DES', 'nr':'NR'}
        data = {}

        with open(performance_fn) as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                suggestion_split_label = row['suggestion_splits']
                validation_label = row['testing_strategy']
                feature_label = row['feature']
                method_label = row['method']
                try:
                    err20 = float(row['ERR@20'])
                except:
                    continue
                try:
                    p5 = float(row['P@5'])
                except:
                    continue

                if method_label not in allowed_methods:
                    continue
                if 'AllUser' in suggestion_split_label:
                    continue
                if 'without_validation' in validation_label:
                    continue
                if feature_label not in feature_label_mapping:
                    continue

                feature_label = feature_label_mapping[feature_label]

                if 'ERR@20' not in data:
                    data['ERR@20'] = {}
                if feature_label not in data['ERR@20']:
                    data['ERR@20'][feature_label] = {}
                data['ERR@20'][feature_label][suggestion_split_label] = err20
                if 'P@5' not in data:
                    data['P@5'] = {}
                if feature_label not in data['P@5']:
                    data['P@5'][feature_label] = {}
                data['P@5'][feature_label][suggestion_split_label] = p5
        return data


    def plot_optimal_with_less_data(self):
        self.plot_less_data(self.load_optimal_data(), 'optimal')

    def plot_suboptimal_with_less_data(self):
        self.plot_less_data(self.load_suboptimal_data(), 'suboptimal')



if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-a", "--plot_optimal_perform_with_less_data",
        nargs=1,
        help="Plots the trend of optimal performance with less data. para: [collection name] ")
    parser.add_argument("-al", "--plot_optimal_perform_with_less_data_all_collections",
        nargs=2,
        help="para: [0|1] whether include suboptimal results && [0|1] whether include LTR results. optimal results will always be shown.")

    parser.add_argument("-b", "--plot_suboptimal_perform_with_less_data",
        nargs=1,
        help="Plots the trend of sub-optimal performance with less data. para: [collection name] ")

    args = parser.parse_args()

    if args.plot_optimal_perform_with_less_data:
        ResultPlots(collection=args.plot_optimal_perform_with_less_data[0]).plot_optimal_with_less_data()
    if args.plot_optimal_perform_with_less_data_all_collections:
        d = {}
        sub_d = {}
        ltr = {}
        for c in collections:
            d[c] = ResultPlots(collection=c).load_optimal_data()
            sub_d[c] = ResultPlots(collection=c).load_suboptimal_data()
            ltr[c] = ResultPlots(collection=c).load_ltr_data()
        #print ltr
        ResultPlots(collection='yelp').plot_less_data_all_collections(d, 'less-data-all', \
                args.plot_optimal_perform_with_less_data_all_collections[0]!='0', sub_d \
                , args.plot_optimal_perform_with_less_data_all_collections[1]!='0', ltr)

    if args.plot_suboptimal_perform_with_less_data:
        ResultPlots(collection=args.plot_suboptimal_perform_with_less_data[0]).plot_suboptimal_with_less_data()

