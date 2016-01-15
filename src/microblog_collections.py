import query
import evaluation
import microblog

query = [ 
  {
    "collection": "microblog2013",
    "collection_formal_name": "MB13",
    "query_class": query.MicroBlogQuery,
    "evaluation_class": evaluation.Evaluation,
    "cnt": 60,
    "qf_parts": ['query'],
    "qrel_program": 'trec_eval -m all_trec -q',
    "main_metric": "MAP"
  }
]
