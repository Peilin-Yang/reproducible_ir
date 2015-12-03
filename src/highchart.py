# -*- coding: utf-8 -*-
import sys,os
import json
import re
import random
from string import Template
import itertools
from subprocess import Popen, PIPE
from inspect import currentframe, getframeinfo
import argparse

reload(sys)
sys.setdefaultencoding('utf-8')


content_template = Template("""

<html>

<head>
    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.8.2/jquery.min.js"></script>
    <script src="http://code.highcharts.com/highcharts.js"></script>

    <script>
    $$(function () {
        $$('#container').highcharts({
            chart: {
                type: 'scatter',
                zoomType: 'xy'
            },
            title: {
                text: '$title'
            },
            subtitle: {
                text: 'Evaluation Method: $eval_method'
            },
            xAxis: {
                title: {
                    enabled: true,
                    text: 'Year'
                },
                startOnTick: true,
                endOnTick: true,
                showLastLabel: true
            },
            yAxis: {
                title: {
                    text: 'Performance'
                }
            },
            legend: {
                enabled: false,
                layout: 'vertical',
                align: 'right',
                verticalAlign: 'bottom',
                y: 100,
                floating: false,
                backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF',
                borderWidth: 1
            },
            plotOptions: {
                scatter: {
                    marker: {
                        radius: 4,
                        states: {
                            hover: {
                                enabled: true,
                                lineColor: 'rgb(100,100,100)'
                            }
                        }
                    },
                    states: {
                        hover: {
                            marker: {
                                enabled: false
                            }
                        }
                    },
                    tooltip: {
                        headerFormat: '<b>{series.name}</b><br>'
                    }
                }
            },
            series: $data
        });
    });
</script>

</head>

<body>
    <div id="container" style="width:100%; height:700px;"></div>
</body>

</html>

""")

class Highchart(object):
    """
    Handle the results. For example, merge the split results.
    When constructing, pass the path of the corpus. For example, "../wt2g/"
    """
    def __init__(self, collection_path):
        self.corpus_path = os.path.abspath(collection_path)
        if not os.path.exists(self.corpus_path):
            frameinfo = getframeinfo(currentframe())
            print frameinfo.filename, frameinfo.lineno
            print '[Evaluation Constructor]:Please provide a valid corpus path'
            exit(1)

        self.performances_root = os.path.join(self.corpus_path, 'performances')
        self.highcharts_root = os.path.join(self.corpus_path, 'highcharts')
        if not os.path.exists(self.highcharts_root):
            os.makedirs(self.highcharts_root)

    def load_all_methods(self):
        all_methods = {}
        with open('g.json') as f:
            methods = json.load(f)['methods']
            for m in methods:
                all_methods[m['name']] = m

        return all_methods

    def gen_output_highcharts_paras(self):
        """
        all_methods: a dict which is essentially the json content of the file `g.json`
        """
        all_paras = []
        all_results = {}
        for fn in os.listdir(self.performances_root):
            #print fn
            query_part = fn.split('-')[0]
            method = fn.split('-')[1]
            if query_part not in all_results:
                all_results[query_part] = []
            all_results[query_part].append( os.path.join(self.performances_root, fn) )

        for query_part in all_results:
            tmp = [self.corpus_path, os.path.join(self.highcharts_root, query_part)]
            tmp.extend( all_results[query_part] )
            all_paras.append(tmp)

        return all_paras


    def output_highcharts(self, output_folder, input_fns):
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        all_performances = {}
        all_methods = self.load_all_methods()
        
        for fn in input_fns:
            query_part = fn.split('-')[0]
            method = fn.split('-')[1]
            with open(fn) as f:
                j = json.load(f)
                for eval_method in j:
                    if eval_method not in all_performances:
                        all_performances[eval_method] = []
                    all_performances[eval_method].append( 
                      {
                        'method': method, 
                        'performance': j[eval_method]['max']['value'],
                        'para': j[eval_method]['max']['para'],
                        'year': all_methods[method]['year'],
                        'paper': all_methods[method]['paper']
                      } 
                    )

        collection_name = output_folder.split('/')[-3]
        query_part = output_folder.split('/')[-1]

        for eval_method in all_performances:
            all_performances[eval_method].sort(key=lambda s: s['year'])
            data = '['
            for ele in all_performances[eval_method]:
                data += '{name: "%s", \n color: "rgba(%d, %d, %d, .9)", \n data:[[%d, %f]]},' % \
                    (
                        'method:'+ele['method']+'<br><b>'+eval_method+':'+str(round(ele['performance'], 4))+'</b><br><b>'+'para:'+ele['para']+'</b><br><b>'+'year:'+str(ele['year'])+'</b><br><b>'+'paper:'+ele['paper']+'</b>',
                        random.randint(1, 255),
                        random.randint(1, 255),
                        random.randint(1, 255),
                        ele['year'],
                        ele['performance']
                    )
            data += ']'
            with open(os.path.join(output_folder, collection_name+'-'+eval_method+'.html'), 'wb') as f:
                f.write(
                    content_template.substitute(
                        title=collection_name+'-'+query_part,
                        eval_method=eval_method,
                        data=data
                    )
                )


if __name__ == '__main__':
    pass

