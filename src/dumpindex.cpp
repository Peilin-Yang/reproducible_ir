/*==========================================================================
 * Copyright (c) 2004 University of Massachusetts.  All Rights Reserved.
 *
 * Use of the Lemur Toolkit for Language Modeling and Information Retrieval
 * is subject to the terms of the software license set forth in the LICENSE
 * file included with this software, and also available at
 * http://www.lemurproject.org/license.html
 *
 *==========================================================================
*/

//
// dumpindex
//
// 13 September 2004 -- tds
//

#include "indri/Repository.hpp"
#include "indri/CompressedCollection.hpp"
#include "indri/LocalQueryServer.hpp"
#include "indri/ScopedLock.hpp"
#include "indri/QueryEnvironment.hpp"
#include <iostream>
#include <climits>
#include <fstream>
#include <sstream>
#include <string>
#include <cmath>

#include "indri/change_peilin.hpp"

double cal_avg(std::vector<double>& l) {
  double s = 0.0;
  for (size_t i = 0; i != l.size(); ++i) {
    s += l[i];
  }
  return s/l.size();
}

double cal_variance(std::vector<double>& l, double avg) {
  double s = 0.0;
  for (size_t i = 0; i != l.size(); ++i) {
    s += (l[i]-avg) * (l[i]-avg);
  }
  return s/l.size();
}

double cal_std(std::vector<double>& l, double avg) {
  return sqrt(cal_variance(l, avg));
}



void print_document_expression_count( const std::string& indexName, const std::string& expression ) {
  indri::api::QueryEnvironment env;
  // compute the expression list using the QueryEnvironment API
  env.addIndex( indexName );
  double result = env.documentExpressionCount( expression );
  env.close();
  std::cout << expression << ":" << result << std::endl;
}

void print_expression_count( const std::string& indexName, const std::string& expression ) {
  indri::api::QueryEnvironment env;

  // compute the expression list using the QueryEnvironment API
  env.addIndex( indexName );
  double result = env.expressionCount( expression );
  env.close();

  std::cout << expression << ":" << result << std::endl;
}

void print_expression_list( const std::string& indexName, const std::string& expression ) {
  indri::api::QueryEnvironment env;

  // compute the expression list using the QueryEnvironment API
  env.addIndex( indexName );
  std::vector<indri::api::ScoredExtentResult> result = env.expressionList( expression );


  std::cout << expression << " " << env.termCount() << " " 
            << env.documentCount() << std::endl;

  env.close();
  // now, print the results in the format:
  // documentID weight begin end
  for( size_t i=0; i<result.size(); i++ ) {
    std::cout << result[i].document
              << " " 
              << result[i].score
              << " " 
              << result[i].begin
              << " " 
              << result[i].end
              << std::endl;
  }
}

//
// Attempts to validate the index.  Right now it only checks
// TermLists, but may do more in the future.
//

void validate( indri::collection::Repository& r ) {
  indri::collection::Repository::index_state state = r.indexes();
  indri::index::Index* index = (*state)[0];

  indri::index::TermListFileIterator* iter = index->termListFileIterator();
  int document = 1;
  iter->startIteration();

  while( !iter->finished() ) {
    indri::index::TermList* list = iter->currentEntry();
    
    if( list->terms().size() != index->documentLength( document ) ) {
      std::cout << "Document " << document << " length mismatch" << std::endl;
    }

    std::cout << document << std::endl;
    const indri::index::TermList* flist = index->termList( document );

    if( flist->terms().size() != list->terms().size() ) {
      std::cout << "Fetched version of term list is different for " << document << std::endl;
    }
    delete flist;

    document++;
    iter->nextEntry();
  }

  if( (document-1) != index->documentCount() ) {
    std::cout << "Document count (" << index->documentCount() << ") does not match term list count " << (document-1) << std::endl;
  }

  delete iter;
}

//
// Print the whole inverted file.  Each term entry starts with 
// a term statistics header (term, termCount, documentCount)
// followed by indented rows (one per document) of the form:
// (document, numPositions, pos1, pos2, ... posN ).
//

void print_invfile( indri::collection::Repository& r ) {
  indri::collection::Repository::index_state state = r.indexes();

  indri::index::Index* index = (*state)[0];
  indri::index::DocListFileIterator* iter = index->docListFileIterator();
  iter->startIteration();
  std::cout << index->termCount() << " " << index->documentCount() << std::endl;

  while( !iter->finished() ) {
    indri::index::DocListFileIterator::DocListData* entry = iter->currentEntry();
    indri::index::TermData* termData = entry->termData;
 
    entry->iterator->startIteration();

    std::cout << termData->term << " "
              << termData->corpus.totalCount << " " //total occurence of this term in the collection
              << termData->corpus.documentCount <<  std::endl; //total number of documents that contains this term in the collection

    while( !entry->iterator->finished() ) {
      indri::index::DocListIterator::DocumentData* doc = entry->iterator->currentEntry();

      #ifdef ADD_AVG_TF_TO_INDEX
      std::cout << "\tdocument:" << doc->document << " uniqueTermCounts:" << doc->uniqueTermCounts<< " positions:" << doc->positions.size();
      #else
      std::cout << "\t" << doc->document << " " << doc->positions.size();
      #endif
      for( size_t i=0; i<doc->positions.size(); i++ ) {
        std::cout << " " << doc->positions[i];
      }
      std::cout << std::endl;

      entry->iterator->nextEntry();
    }

    iter->nextEntry();
  }

  delete iter;
}


// 
// Prints the vocabulary statistics.
//

void print_vocabulary_stats( indri::collection::Repository& r ) {
  indri::collection::Repository::index_state state = r.indexes();

  indri::index::Index* index = (*state)[0];
  indri::index::VocabularyIterator* iter = index->vocabularyIterator();

  iter->startIteration();
  //std::cout << "TOTAL" << " " << index->termCount() << " " << index->documentCount() << std::endl;

  UINT64 total = 0;
  UINT64 max_df = 0;
  UINT64 min_df = ULLONG_MAX;
  double sum_df = 0.0;
  double avg_df = 0.0;
  double var_df = 0.0;
  std::vector<double> all_dfs;

  UINT64 max_tfc = 0; //term frequency in collection
  UINT64 min_tfc = ULLONG_MAX;
  double sum_tfc = 0.0;
  double avg_tfc = 0.0;
  double var_tfc = 0.0;
  std::vector<double> all_tfcs;

  while( !iter->finished() ) {
    indri::index::DiskTermData* entry = iter->currentEntry();
    indri::index::TermData* termData = entry->termData;
    /*
      std::cout << termData->term << " "
              << termData->corpus.totalCount << " " //total occurence of this term in the collection
              << termData->corpus.documentCount <<  std::endl; //total number of documents that contains this term in the collection
       */
    // DF start
    if(termData->corpus.documentCount > max_df) {
      max_df = termData->corpus.documentCount;
    }
    if(termData->corpus.documentCount < min_df) {
      min_df = termData->corpus.documentCount;
    }
    sum_df += termData->corpus.documentCount;
    all_dfs.push_back(termData->corpus.documentCount*1.0);
    //DF end

    // TFC start
    if(termData->corpus.totalCount > max_tfc) {
      max_tfc = termData->corpus.totalCount;
    }
    if(termData->corpus.totalCount < min_tfc) {
      min_tfc = termData->corpus.totalCount;
    }
    sum_tfc += termData->corpus.totalCount;
    all_tfcs.push_back(termData->corpus.totalCount*1.0);
    // TFC end

    total++;
    iter->nextEntry();
  }

  avg_df = sum_df/total;
  var_df = cal_variance( all_dfs, avg_df);

  avg_tfc = sum_tfc/total;
  var_tfc = cal_variance( all_tfcs, avg_tfc);

  delete iter;


  cout << "{"<< endl;
  cout << "\"total\":"<<total<<","<<endl;
  cout << "\"maxDF\":"<<max_df<<","<<endl;
  cout << "\"minDF\":"<<min_df<<","<<endl;
  cout << "\"sumDF\":"<<sum_df<<","<<endl;
  cout << "\"avgDF\":"<<avg_df<<","<<endl;
  cout << "\"varDF\":"<<var_df<<","<<endl;
  cout << "\"maxTFC\":"<<max_tfc<<","<<endl;
  cout << "\"minTFC\":"<<min_tfc<<","<<endl;
  cout << "\"sumTFC\":"<<sum_tfc<<","<<endl;
  cout << "\"avgTFC\":"<<avg_tfc<<","<<endl;
  cout << "\"varTFC\":"<<var_tfc<<endl;
  cout << "}"<<endl;
}



// 
// Prints the vocabulary of the index, including term statistics.
//

void print_vocabulary( indri::collection::Repository& r ) {
  indri::collection::Repository::index_state state = r.indexes();

  indri::index::Index* index = (*state)[0];
  indri::index::VocabularyIterator* iter = index->vocabularyIterator();

  iter->startIteration();
  std::cout << "TOTAL" << " " << index->termCount() << " " << index->documentCount() << std::endl;

  while( !iter->finished() ) {
    indri::index::DiskTermData* entry = iter->currentEntry();
    indri::index::TermData* termData = entry->termData;

    std::cout << termData->term << " "
              << termData->corpus.totalCount << " " //total occurence of this term in the collection
              << termData->corpus.documentCount <<  std::endl; //total number of documents that contains this term in the collection
    iter->nextEntry();
  }

  delete iter;
}

void print_field_positions( indri::collection::Repository& r, const std::string& fieldString ) {
  indri::server::LocalQueryServer local(r);

  UINT64 totalCount = local.termCount();

  std::cout << fieldString << std::endl;

  indri::collection::Repository::index_state state = r.indexes();

  for( size_t i=0; i<state->size(); i++ ) {
    indri::index::Index* index = (*state)[i];
    indri::thread::ScopedLock( index->iteratorLock() );

    indri::index::DocExtentListIterator* iter = index->fieldListIterator( fieldString );
    if (iter == NULL) continue;
    
    iter->startIteration();

    int doc = 0;
    indri::index::DocExtentListIterator::DocumentExtentData* entry;

    for( iter->startIteration(); iter->finished() == false; iter->nextEntry() ) {
      entry = iter->currentEntry();

      std::cout << entry->document << " "
                << entry->extents.size() << " "
                << index->documentLength( entry->document ) << " ";

      size_t count = entry->extents.size();

      for( size_t i=0; i<count; i++ ) {
        std::cout << " ( " << entry->extents[i].begin << ", " << entry->extents[i].end;
        if( entry->numbers.size() ) {
          std::cout << ", " << entry->numbers[i];
        }
        std::cout << " ) ";
      }

      std::cout << std::endl;
    }

    delete iter;
  }
}

void print_term_positions( indri::collection::Repository& r, const std::string& termString ) {
  std::string stem = r.processTerm( termString );
  indri::server::LocalQueryServer local(r);

  UINT64 totalCount = local.termCount();
  UINT64 termCount = local.termCount( termString );

  std::cout << termString << " "
            << stem << " "
            << termCount << " " 
            << totalCount << " " << std::endl;

  indri::collection::Repository::index_state state = r.indexes();

  for( size_t i=0; i<state->size(); i++ ) {
    indri::index::Index* index = (*state)[i];
    indri::thread::ScopedLock( index->iteratorLock() );

    indri::index::DocListIterator* iter = index->docListIterator( stem );
    if (iter == NULL) continue;
    
    iter->startIteration();

    int doc = 0;
    indri::index::DocListIterator::DocumentData* entry;

    for( iter->startIteration(); iter->finished() == false; iter->nextEntry() ) {
      entry = (indri::index::DocListIterator::DocumentData*) iter->currentEntry();

      std::cout << entry->document << " "
                << entry->positions.size() << " "
                << index->documentLength( entry->document ) << " ";

      size_t count = entry->positions.size();

      for( size_t i=0; i<count; i++ ) {
        std::cout << entry->positions[i] << " ";
      }

      std::cout << std::endl;
    }

    delete iter;
  }
}

void print_term_counts( indri::collection::Repository& r, const std::string& termString ) {
  std::string stem = r.processTerm( termString );
  indri::server::LocalQueryServer local(r);

  UINT64 totalCount = local.termCount();
  UINT64 termCount = local.termCount( termString );

  std::cout << termString << " "
            << stem << " "
            << termCount << " " 
            << totalCount << " " << std::endl;

  indri::collection::Repository::index_state state = r.indexes();
  indri::collection::CompressedCollection* collection = r.collection();
    
  for( size_t i=0; i<state->size(); i++ ) {
    indri::index::Index* index = (*state)[i];
    indri::thread::ScopedLock( index->iteratorLock() );

    indri::index::DocListIterator* iter = index->docListIterator( stem );
    if (iter == NULL) continue;

    iter->startIteration();

    int doc = 0;
    indri::index::DocListIterator::DocumentData* entry;

    for( iter->startIteration(); iter->finished() == false; iter->nextEntry() ) {
      entry = iter->currentEntry();

      std::cout << entry->document << " "
                << collection->retrieveMetadatum( entry->document, "docno") << " "
                << entry->positions.size() << " "
                << index->documentLength( entry->document ) << std::endl;
      doc++;
    }

    cout << "total doc:" << doc << endl;
    delete iter;
  }
}

void print_term_feature( indri::collection::Repository& r, const std::string& termString) {
  std::string stem = r.processTerm( termString );
  indri::server::LocalQueryServer local(r);
  UINT64 totalCount = local.termCount();
  UINT64 docCount = local.documentCount();
  indri::collection::Repository::index_state state = r.indexes();

  int total_doc_occur = 0;
  unsigned int maxTF = 0;
  unsigned int minTF = 4294967295U;
  double sum_tf = 0.0;
  double avg_tf = 0.0;
  double var_tf = 0.0;
  std::vector<double> all_tfs;
  for( size_t i=0; i<state->size(); i++ ) {
    indri::index::Index* index = (*state)[i];
    indri::thread::ScopedLock( index->iteratorLock() );

    indri::index::DocListIterator* iter = index->docListIterator( stem );
    if (iter == NULL) continue;

    iter->startIteration();
    
    indri::index::DocListIterator::DocumentData* entry;

    for( iter->startIteration(); iter->finished() == false; iter->nextEntry() ) {
      entry = iter->currentEntry();
      int thisTF = entry->positions.size();
      all_tfs.push_back(thisTF*1.0);
      sum_tf += thisTF;
      if (thisTF > maxTF) {
        maxTF = thisTF;
      }
      if (thisTF < minTF) {
        minTF = thisTF;
      }
      total_doc_occur++;
    }

    delete iter;
  }

  avg_tf = sum_tf/total_doc_occur;
  var_tf = cal_variance(all_tfs, avg_tf);


  cout << "{"<< endl;
  cout << "\"raw\":"<<"\""<<termString<<"\","<<endl;
  cout << "\"stem\":"<<"\""<<stem<<"\","<<endl;
  cout << "\"collection_doc_count\":"<<docCount<<","<<endl;
  cout << "\"collection_term_count\":"<<totalCount<<","<<endl;
  cout << "\"df\":"<<total_doc_occur<<","<<endl;
  cout << "\"idf1\":"<<(docCount * 1.0) / (total_doc_occur + 0.000001)<<","<<endl;
  cout << "\"log(idf1)\":"<<log((docCount * 1.0) / (total_doc_occur + 0.000001))<<","<<endl;
  cout << "\"maxTF\":"<<maxTF<<","<<endl;
  cout << "\"minTF\":"<<minTF<<","<<endl;
  cout << "\"avgTF\":"<<avg_tf<<","<<endl;
  cout << "\"varTF\":"<<var_tf<<endl;
  cout << "}"<<endl;
  
}

void print_document_name( indri::collection::Repository& r, const char* number ) {
  indri::collection::CompressedCollection* collection = r.collection();
  //  std::string documentName = collection->retrieveMetadatum( atoi( number ), "docid" );
  std::string documentName = collection->retrieveMetadatum( atoi( number ), "docno" );
  std::cout << documentName << std::endl;
}

void print_document_text( indri::collection::Repository& r, const char* number ) {
  int documentID = atoi( number );
  indri::collection::CompressedCollection* collection = r.collection();
  indri::api::ParsedDocument* document = collection->retrieve( documentID );

  std::cout << document->text << std::endl;
  delete document;
}

void print_document_data( indri::collection::Repository& r, const char* number ) {
  int documentID = atoi( number );
  indri::collection::CompressedCollection* collection = r.collection();
  indri::api::ParsedDocument* document = collection->retrieve( documentID );

  std::cout << std::endl << "--- Metadata ---" << std::endl << std::endl;

  for( size_t i=0; i<document->metadata.size(); i++ ) {
    if( document->metadata[i].key[0] == '#' )
      continue;

    std::cout << document->metadata[i].key << ": "
              << (const char*) document->metadata[i].value
              << std::endl;
  }

  std::cout << std::endl << "--- Positions ---" << std::endl << std::endl;

  for( size_t i=0; i<document->positions.size(); i++ ) {
    std::cout << i << " "
              << document->positions[i].begin << " "
              << document->positions[i].end << std::endl;

  }

  std::cout << std::endl << "--- Tags ---" << std::endl << std::endl;

  for( size_t i=0; i<document->tags.size(); i++ ) {
    std::cout << i << " "
              << document->tags[i]->name << " " 
              << document->tags[i]->begin << " "
              << document->tags[i]->end << " " 
              << document->tags[i]->number << std::endl;
  }

  std::cout << std::endl << "--- Text ---" << std::endl << std::endl;
  std::cout << document->text << std::endl;

  std::cout << std::endl << "--- Content ---" << std::endl << std::endl;
  std::cout << document->getContent() << std::endl;

  delete document;
}


std::vector<lemur::api::DOCID_T> read_document_internal_ids_from_file(const char* filename) 
{
    std::vector<lemur::api::DOCID_T> docids;
    std::ifstream infile(filename);
    std::string line;
    while (std::getline(infile, line))
    {
        std::istringstream iss(line);
        string internal_docid;
        if (!(iss >> internal_docid)) { continue; } // error

        docids.push_back(atoi(line.c_str()));
    }

    //for (int i = 0; i != docids.size(); ++i) {
    //    cout << docids[i] << endl;
    //}

    return docids;
}

void print_document_stats( indri::collection::Repository& r, const char* fn ) 
// fn: filename that contains external docids line by line
{
    std::vector<lemur::api::DOCID_T> internal_docids = read_document_internal_ids_from_file(fn);

    indri::server::LocalQueryServer local(r);
    indri::server::QueryServerVectorsResponse* response = local.documentVectors( internal_docids );
    
    for( size_t i = 0; i != response->getResults().size(); ++i ) {
      indri::api::DocumentVector* docVector = response->getResults()[i];
      std::map<string, unsigned int> docMap;
      std::vector<double> all_tfs;
      unsigned int maxTF = 0;
      unsigned int minTF = 4294967295U;
      double sum_tf = 0.0;
      double avg_tf = 0.0;
      double var_tf = 0.0;
      for( size_t j=0; j != docVector->positions().size(); ++j ) {
        int position = docVector->positions()[j];
        const std::string& stem = docVector->stems()[position];
        if (docMap.count(stem)) {
          docMap[stem]++;
        } else {
          docMap[stem] = 1;
        }
        sum_tf += 1;
      }

      for (std::map<string, unsigned int>::iterator it=docMap.begin(); it!=docMap.end(); ++it) {
        if (it->second > maxTF) {
          maxTF = it->second;
        }
        if (it->second < minTF) {
          minTF = it->second;
        }
        all_tfs.push_back(it->second);
      }
      avg_tf = sum_tf/docMap.size();
      var_tf = cal_variance( all_tfs, avg_tf);

      cout << "id:" << internal_docids[i] << ",minTF:" << minTF \ 
        << ",maxTF:" << maxTF << ",sumTF:" << sum_tf \
        << ",avgTF:" << avg_tf << ",varTF:" << var_tf << endl;
      delete docVector;
    }
    
    delete response;
}

void print_all_document_stats( indri::collection::Repository& r ) 
// fn: filename that contains external docids line by line
{
    indri::server::LocalQueryServer local(r);
    UINT64 docCount = local.documentCount();
    vector<double> all_maxTF;
    vector<double> all_minTF;
    vector<double> all_avgTF;
    vector<double> all_stdTF;
    std::vector<lemur::api::DOCID_T> docids;
    for( size_t i=1; i<docCount+1; i++ ) {
      docids.push_back(i);
      if (docids.size() >= 500 || i == docCount) {
        indri::server::QueryServerVectorsResponse* response = local.documentVectors( docids );
        for( size_t i = 0; i != response->getResults().size(); ++i ) {
          indri::api::DocumentVector* docVector = response->getResults()[i];
          std::map<string, UINT64> docMap;
          std::vector<double> all_tfs;
          long long maxTF = 0;
          long long minTF = 4294967295U;
          double sum_tf = 0.0;
          double avg_tf = 0.0;
          double std_tf = 0.0;
          for( size_t j=0; j != docVector->positions().size(); ++j ) {
            int position = docVector->positions()[j];
            const std::string& stem = docVector->stems()[position];
            if (docMap.count(stem)) {
              docMap[stem]++;
            } else {
              docMap[stem] = 1;
            }
            sum_tf += 1;
          }

          for (std::map<string, UINT64>::iterator it=docMap.begin(); it!=docMap.end(); ++it) {
            if (it->second > maxTF) {
              maxTF = it->second;
            }
            if (it->second < minTF) {
              minTF = it->second;
            }
            all_tfs.push_back(it->second);
          }
          avg_tf = docMap.empty()?0:sum_tf/docMap.size();
          std_tf = docMap.empty()?0:cal_std( all_tfs, avg_tf);
          /*cout << "id:" << internal_docids[i] << ",minTF:" << minTF \ 
            << ",maxTF:" << maxTF << ",sumTF:" << sum_tf \
            << ",avgTF:" << avg_tf << ",varTF:" << var_tf << endl;*/
          all_minTF.push_back(minTF==4294967295U?0:minTF);
          all_maxTF.push_back(maxTF);
          all_avgTF.push_back(avg_tf);
          all_stdTF.push_back(std_tf);
          delete docVector;
        }
        delete response;
        docids.clear();
      }
    }

    //cout << all_minTF.size() << endl;
    double avg_all_minTF = cal_avg(all_minTF);
    cout << "avg_minTF:" << avg_all_minTF << endl;
    cout << "std_minTF:" << cal_std(all_minTF, avg_all_minTF) << endl;
    double avg_all_maxTF = cal_avg(all_maxTF);
    cout << "avg_maxTF:" << avg_all_maxTF << endl;
    cout << "std_maxTF:" << cal_std(all_maxTF, avg_all_maxTF) << endl;
    double avg_all_avgTF = cal_avg(all_avgTF);
    cout << "avg_avgTF:" << avg_all_avgTF << endl;
    cout << "std_avgTF:" << cal_std(all_avgTF, avg_all_avgTF) << endl;
    double avg_all_stdTF = cal_avg(all_stdTF);
    cout << "avg_stdTF:" << avg_all_stdTF << endl;
    cout << "std_stdTF:" << cal_std(all_stdTF, avg_all_stdTF) << endl;
}

void print_document_vector( indri::collection::Repository& r, const char* number ) {
  indri::server::LocalQueryServer local(r);
  lemur::api::DOCID_T documentID = atoi( number );

  std::vector<lemur::api::DOCID_T> documentIDs;
  documentIDs.push_back(documentID);

  indri::server::QueryServerVectorsResponse* response = local.documentVectors( documentIDs );
  
  if( response->getResults().size() ) {
    indri::api::DocumentVector* docVector = response->getResults()[0];
  
    std::cout << "--- Fields ---" << std::endl;

    for( size_t i=0; i<docVector->fields().size(); i++ ) {
      const indri::api::DocumentVector::Field& field = docVector->fields()[i];
      std::cout << field.name << " " << field.begin << " " << field.end << " " << field.number << std::endl;
    }

    std::cout << "--- Terms ---" << std::endl;

    for( size_t i=0; i<docVector->positions().size(); i++ ) {
      int position = docVector->positions()[i];
      const std::string& stem = docVector->stems()[position];

      #ifdef INDEX_ADD_TERM_RELATIVE_POSITION
      int relative_position = docVector->relative_positions()[i];
      std::cout << i << " " << position << " " << relative_position << " " << stem << std::endl;
      #else
      std::cout << i << " " << position << " " << stem << std::endl;
      #endif
    }

    delete docVector;
  }

  delete response;
}

void print_document_id( indri::collection::Repository& r, const char* an, const char* av ) {
  indri::collection::CompressedCollection* collection = r.collection();
  std::string attributeName = an;
  std::string attributeValue = av;
  std::vector<lemur::api::DOCID_T> documentIDs;

  documentIDs = collection->retrieveIDByMetadatum( attributeName, attributeValue );

  for( size_t i=0; i<documentIDs.size(); i++ ) {
    std::cout << documentIDs[i] << std::endl;
  }
}

void print_repository_stats( indri::collection::Repository& r ) {
  indri::server::LocalQueryServer local(r);
  UINT64 termCount = local.termCount();
  UINT64 docCount = local.documentCount();
  std::vector<std::string> fields = local.fieldList();
  indri::collection::Repository::index_state state = r.indexes();
  UINT64 uniqueTermCount = 0;
  for( size_t i=0; i<state->size(); i++ ) {
    indri::index::Index* index = (*state)[i];
    uniqueTermCount += index->uniqueTermCount();
  }
  std::cout << "Repository statistics:\n"
            << "documents:\t" << docCount << "\n"
            << "unique terms:\t" << uniqueTermCount    << "\n"
            << "total terms:\t" << termCount    << "\n"
            << "average doc length:\t" << termCount*1.0/docCount    << "\n"
            << "fields:\t\t";
  for( size_t i=0; i<fields.size(); i++ ) {
    std::cout << fields[i] << " ";
  }
  std::cout << std::endl;
}


void print_rich_repository_stats( indri::collection::Repository& r ) {
  indri::server::LocalQueryServer local(r);
  UINT64 termCount = local.termCount();
  UINT64 docCount = local.documentCount();
  double avg_doc_len = termCount*1.0/docCount;
  std::vector<std::string> fields = local.fieldList();
  indri::collection::Repository::index_state state = r.indexes();
  UINT64 uniqueTermCount = 0;
  for( size_t i=0; i<state->size(); i++ ) {
    indri::index::Index* index = (*state)[i];
    uniqueTermCount += index->uniqueTermCount();
    /*indri::index::DocListFileIterator* iter = index->docListFileIterator();
    iter->startIteration();
    //std::cout << index->termCount() << " " << index->documentCount() << std::endl;
    while( !iter->finished() ) {
      indri::index::DocListFileIterator::DocListData* entry = iter->currentEntry();
      indri::index::DocListIterator::DocumentData* doc = entry->iterator->currentEntry();
      all_doc_len.push_back(index->documentLength( doc->document )*1.0);
      iter->nextEntry();
    }
    delete iter;*/
  }

  std::vector<double> all_doc_len;
  for( size_t i=1; i<docCount+1; i++ ) {
    all_doc_len.push_back(local.documentLength(i)*1.0);
  }
  
  double std_doc_len = cal_std(all_doc_len, avg_doc_len);
  double avg_doc_len2 = cal_avg(all_doc_len);

  std::cout << "{\n"
        << "\"documents\":" << docCount << ",\n"
        << "\"unique terms\":" << uniqueTermCount    << ",\n"
        << "\"total terms\":" << termCount    << ",\n"
        << "\"average doc length\":" << avg_doc_len << ",\n"
        //<< "\"documents2\":" << all_doc_len.size() << ",\n"
        //<< "\"average doc length2\":" << avg_doc_len2 << ",\n"
        << "\"std doc length\":" << std_doc_len << "\n";

  #if 0
  // The rich statistics part -- Start
  std::map<string,int> all_terms;
  std::map<int,int> all_documents;
  indri::index::Index* index = (*state)[0];
  indri::index::DocListFileIterator* iter = index->docListFileIterator();
  iter->startIteration();
  //std::cout << index->termCount() << " " << index->documentCount() << std::endl;

  while( !iter->finished() ) {
    indri::index::DocListFileIterator::DocListData* entry = iter->currentEntry();
    indri::index::TermData* termData = entry->termData;
 
    entry->iterator->startIteration();
    all_terms[string(termData->term)] = termData->corpus.totalCount;
    while( !entry->iterator->finished() ) {
      indri::index::DocListIterator::DocumentData* doc = entry->iterator->currentEntry();
      all_documents[doc->document] = index->documentLength( doc->document );
      entry->iterator->nextEntry();
    }

    iter->nextEntry();
  }

  delete iter;

  std::string allTermsStr("");
  std::string allDocsStr("");

  allTermsStr += "\"allTerms\":{\n";
  for (std::map<string,int>::iterator it=all_terms.begin(); it!=all_terms.end(); ++it){
    std::stringstream ss;
    ss << "\"" << it->first << "\":" << it->second << ",\n";
    allTermsStr += ss.str();
  }
  allTermsStr = allTermsStr.substr(0, allTermsStr.size()-2);
  allTermsStr += "\n},\n";
  
  std::cout << allTermsStr;


  allDocsStr += "\"allDocs\":{\n";
  for (std::map<int,int>::iterator it=all_documents.begin(); it!=all_documents.end(); ++it){
    std::stringstream ss;
    ss << "\"" << it->first << "\":" << it->second << ",\n";
    allDocsStr += ss.str();
  }
  allDocsStr = allDocsStr.substr(0, allDocsStr.size()-2);
  allDocsStr += "\n}\n";
  
  std::cout << allDocsStr;
  #endif
    
  std::cout << "}\n";
}


void merge_repositories( const std::string& outputPath, int argc, char** argv ) {
  std::vector<std::string> inputs;

  for( int i=3; i<argc; i++ ) {
    inputs.push_back( argv[i] );
  }

  indri::collection::Repository::merge( outputPath, inputs );
}

void compact_repository( const std::string& repositoryPath ) {
  indri::collection::Repository r;
  r.open( repositoryPath );
  r.compact();
  r.close();
}

void delete_document( const std::string& repositoryPath, const char* stringDocumentID ) {
  lemur::api::DOCID_T documentID = (lemur::api::DOCID_T) string_to_i64( stringDocumentID );
  indri::collection::Repository r;
  r.open( repositoryPath );
  r.deleteDocument( documentID );
  r.close();
}

void usage() {
  std::cout << "dumpindex <repository> <command> [ <argument> ]*" << std::endl;
  std::cout << "These commands retrieve data from the repository: " << std::endl;
  std::cout << "    Command              Argument       Description" << std::endl;
  std::cout << "    term (t)             Term text      Print inverted list for a term" << std::endl;
  std::cout << "    term features(tf)             Term text      Print the feature of a term" << std::endl;
  std::cout << "    showfeature (sf)             Term, Feature      Print the Feature value of Term" << std::endl;
  std::cout << "    termpositions (tp)   Term text      Print inverted list for a term, with positions" << std::endl;
  std::cout << "    fieldpositions (fp)  Field name     Print inverted list for a field, with positions" << std::endl;
  std::cout << "    expressionlist (e)   Expression     Print inverted list for an Indri expression, with positions" << std::endl;
  std::cout << "    xcount (x)           Expression     Print count of occurrences of an Indri expression" << std::endl;
  std::cout << "    dxcount (dx)         Expression     Print document count of occurrences of an Indri expression" << std::endl;
  std::cout << "    documentid (di)      Field, Value   Print the document IDs of documents having a metadata field matching this value" << std::endl;
  std::cout << "    documentname (dn)    Document ID    Print the text representation of a document ID" << std::endl;
  std::cout << "    documenttext (dt)    Document ID    Print the text of a document" << std::endl;
  std::cout << "    documentdata (dd)    Document ID    Print the full representation of a document" << std::endl;
  std::cout << "    documentvector (dv)  Document ID    Print the document vector of a document" << std::endl;
  std::cout << "    invlist (il)         None           Print the contents of all inverted lists" << std::endl;
  std::cout << "    vocabulary (v)       None           Print the vocabulary of the index" << std::endl;
  std::cout << "    vocabulary statistics (vs)       None           Print the vocabulary statistics, e.g. maxDF, avgTFC of the index" << std::endl;
  std::cout << "    stats (s)                           Print statistics for the Repository" << std::endl;
  std::cout << "    rich_stats (rs)                           Print rich statistics for the Repository" << std::endl;
  std::cout << "These commands change the data inside the repository:" << std::endl;
  std::cout << "    compact (c)          None           Compact the repository, releasing space used by deleted documents." << std::endl;
  std::cout << "    delete (del)         Document ID    Delete the specified document from the repository." << std::endl;
  std::cout << "    merge (m)            Input indexes  Merges a list of Indri repositories together into one repository." << std::endl;
}

#define REQUIRE_ARGS(n) { if( argc < n ) { usage(); return -1; } }

int main( int argc, char** argv ) {
  try {
    REQUIRE_ARGS(3);

    indri::collection::Repository r;
    std::string repName = argv[1];
    std::string command = argv[2];

    if( command == "c" || command == "compact" ) {
      REQUIRE_ARGS(3);
      compact_repository( repName );
    } else if( command == "del" || command == "delete" ) {
      REQUIRE_ARGS(4);
      delete_document( repName, argv[3] );
    } else if( command == "m" || command == "merge" ) {
      REQUIRE_ARGS(4);
      merge_repositories( repName, argc, argv );
    } else {
      r.openRead( repName );

      if( command == "t" || command == "term" ) {
        REQUIRE_ARGS(4);
        std::string term = argv[3];
        print_term_counts( r, term );
      } else if( command == "tf" || command == "termfeature" ) {
        REQUIRE_ARGS(4);
        print_term_feature( r, argv[3]);
      } else if( command == "tp" || command == "termpositions" ) { 
        REQUIRE_ARGS(4);
        std::string term = argv[3];
        print_term_positions( r, term );
      } else if( command == "fp" || command == "fieldpositions" ) { 
        REQUIRE_ARGS(4);
        std::string field = argv[3];
        print_field_positions( r, field );
      } else if( command == "e" || command == "expression" ) {
        REQUIRE_ARGS(4);
        std::string expression = argv[3];
        print_expression_list( repName, expression );
      } else if( command == "x" || command == "xcount" ) {
        REQUIRE_ARGS(4);
        std::string expression = argv[3];
        print_expression_count( repName, expression );
      } else if( command == "dx" || command == "dxcount" ) {
        REQUIRE_ARGS(4);
      std::string expression = argv[3];
        print_document_expression_count( repName, expression );
      } else if( command == "dn" || command == "documentname" ) {
        REQUIRE_ARGS(4);
        print_document_name( r, argv[3] );
      } else if( command == "dt" || command == "documenttext" ) {
        REQUIRE_ARGS(4);
        print_document_text( r, argv[3] );
      } else if( command == "dd" || command == "documentdata" ) {
        REQUIRE_ARGS(4);
        print_document_data( r, argv[3] );
      } else if( command == "dv" || command == "documentvector" ) {
        REQUIRE_ARGS(4);
        print_document_vector( r, argv[3] );
      } else if( command == "ds" || command == "documentstats" ) {
        REQUIRE_ARGS(4);
        print_document_stats( r, argv[3] );
      } else if( command == "di" || command == "documentid" ) {
        REQUIRE_ARGS(5);
        print_document_id( r, argv[3], argv[4] );
      } else if( command == "il" || command == "invlist" ) {
        REQUIRE_ARGS(3);
        print_invfile( r );
      } else if( command == "v" || command == "vocabulary" ) {
        REQUIRE_ARGS(3);
        print_vocabulary( r );
      } else if( command == "vs" || command == "vocabularystats" ) {
        REQUIRE_ARGS(3);
        print_vocabulary_stats( r );
      } else if( command == "vtl" || command == "validate" ) {
        REQUIRE_ARGS(3);
        validate(r);
      } else if( command == "s" || command == "stats" ) {
        REQUIRE_ARGS(3);
        print_repository_stats( r );
      } else if( command == "rs" || command == "richstats" ) {
        REQUIRE_ARGS(3);
        print_rich_repository_stats( r );
      } else if( command == "allds" || command == "alldocumentstats" ) {
        REQUIRE_ARGS(3);
        print_all_document_stats( r );
      } else {
        r.close();
        usage();
        return -1;
      }

      r.close();
    }

    return 0;
  } catch( lemur::api::Exception& e ) {
    LEMUR_ABORT(e);
  }
}


