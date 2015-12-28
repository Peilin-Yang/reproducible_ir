import query
import evaluation

query = [ 
  {
    "collection": "disk12",
    "collection_formal_name": "disk12",
    "query_class": query.Query,
    "evaluation_class": evaluation.Evaluation,
    "cnt": 150,
    "qf_parts": ['title'],
    "qrel_program": 'trec_eval -m all_trec -q',
    "main_metric": "MAP"
  }, 
  {
    "collection": "disk45",
    "collection_formal_name": "disk45",
    "query_class": query.Query,
    "evaluation_class": evaluation.Evaluation,
    "cnt": 250,
    "qf_parts": ['title'],
    "qrel_program": 'trec_eval -m all_trec -q',
    "main_metric": "MAP"
  },  
  {
    "collection": "wt2g",
    "collection_formal_name": "WT2G",
    "query_class": query.Query,
    "evaluation_class": evaluation.Evaluation,
    "cnt": 50,
    "qf_parts": ['title'],
    "qrel_program": 'trec_eval -m all_trec -q',
    "main_metric": "MAP"
  },
  {
    "collection": "gov2",
    "collection_formal_name": "GOV2",
    "query_class": query.Query,
    "evaluation_class": evaluation.Evaluation,
    "cnt": 150,
    "qf_parts": ['title'],
    "qrel_program": 'trec_eval -m all_trec -q',
    "main_metric": "MAP"
  }, 
  {
    "collection": "clueweb101112",
    "collection_formal_name": "CW09",
    "query_class": query.ClueWebQuery,
    "evaluation_class": evaluation.EvaluationClueWeb,
    "cnt": 200,
    "qf_parts": ['title'],
    "qrel_program": 'gdeval.pl',
    "main_metric": "ERR@20"
  },
  {
    "collection": "clueweb12",
    "collection_formal_name": "CW12As",
    "query_class": query.ClueWebQuery,
    "evaluation_class": evaluation.EvaluationClueWeb,
    "cnt": 100,
    "qf_parts": ['title'],
    "qrel_program": 'gdeval.pl',
    "main_metric": "ERR@20"
  }
]
