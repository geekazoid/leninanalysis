# This Python file uses the following encoding: utf-8
from __future__ import division
import nltk
import logging
from similarity import path_similarity
from nltk.corpus import wordnet as wn
from information_value.models import *

log = logging.getLogger('lenin')

import config
reload(config)


# Similarity definitions:
# http://nltk.googlecode.com/svn/trunk/doc/api/nltk.corpus.reader.wordnet.Synset-class.html#path_similarity
class WordNetAnalyzer:
    def __init__(self, word, similarity_function = path_similarity ):

        self.word = word
        self.similarity_function = similarity_function

    def judge_list(self, doc_list):
        if doc_list.total_docs == 0:
            return None
        all_docs_with_values = [(doc, self.judge_doc(doc))  for doc in doc_list ]

        if len(all_docs_with_values) == 0:
            return 0

        return (sum(v for (d, v) in all_docs_with_values) / len(all_docs_with_values))   


    def judge_doc(self, document):
        '''
          returns a value between 0 and 1
        '''
        top_words_with_ivs = document.top_words(20)

        ret = 0
        for word, ponderation in top_words_with_ivs:
            word_similarity = self.judge_word(word)

            ret+= ponderation * word_similarity
            log.info("{2:.2f} = word('{1}', '{0}') word-iv: {3:.2f} ".format(word, self.word, ret, ponderation))
            
        if ret > 0.4:
          log.info("{2:.2f} =  doc('{1}', '{0}')".format(document.short_name.encode('utf-8'), self.word, ret))

        return ret


    def judge_word(self, word):
        '''
          calls judge_synset
          @returns double a value between 1.0 and 0.0
        '''
        return self.similarity_function(self.word, word) 

 
def wna_for(word):
    return WordNetAnalyzer(word)



def wnas_for(words):
    res = dict()
    for word in words:
      res[word] = wna_for(word)

    return res


def year_vs_concept_data(concepts = None, year_min = 1899, year_max = 1923):
  
    if not concepts:
        concepts = ["war", "idealism", "revolution", "philosophy"]

    res = dict()

    analyzers = dict((concept, wna_for(concept)) for concept in concepts)

    print "years {0} - {1} vs concepts: {2}. working...".format(year_min, year_max, concepts)
    for year in range(year_min, year_max):
        analyze_year(concepts, analyzers)

    return res

def analyze_year(concepts, analyzers):
    year_res = {}
    for concept in concepts:
      year_res[concept] = _year_vs_concept_analysis(concept, year, analyzers)
    
    log.info("{2:.2f} = year-distance('{1}', '{0}') ".format(year, concept, res[year][concept]))
    output += "{0}: {1:.2f} ".format(concept, res[year][concept])
  
    print "year: {0}, #doc: {1}, res: {2}".format(year, doc_list.total_docs, output)

def _year_vs_concept_analysis(concept, year, analyzers):
    doc_list = DocumentList("", False, year)
    analyzer = analyzers[concept]
    return analyzer.judge_list(doc_list)
