import query
import evaluation

query = [ 
  { 
    "collection": "microblog2011", 
    "collection_formal_name": "MB11",
    "query_class": query.MicroBlogQuery,
    "evaluation_class": evaluation.Evaluation,
    "cnt": 50,
    "qf_parts": ['title'],
    "qrel_program": 'trec_eval -m all_trec -q',
    "main_metric": "MAP"
  },
  { 
    "collection": "microblog2012", 
    "collection_formal_name": "MB12",
    "query_class": query.MicroBlogQuery,
    "evaluation_class": evaluation.Evaluation,
    "cnt": 60,
    "qf_parts": ['title'],
    "qrel_program": 'trec_eval -m all_trec -q',
    "main_metric": "MAP"
  },
  { 
    "collection": "microblog2013", 
    "collection_formal_name": "MB13",
    "query_class": query.MicroBlogQuery,
    "evaluation_class": evaluation.Evaluation,
    "cnt": 60,
    "qf_parts": ['query'],
    "qrel_program": 'trec_eval -m all_trec -q',
    "main_metric": "MAP"
  },
  { 
    "collection": "microblog2014", 
    "collection_formal_name": "MB14",
    "query_class": query.MicroBlogQuery,
    "evaluation_class": evaluation.Evaluation,
    "cnt": 55,
    "qf_parts": ['query'],
    "qrel_program": 'trec_eval -m all_trec -q',
    "main_metric": "MAP"
  }
]
