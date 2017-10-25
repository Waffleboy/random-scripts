#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 11:49:28 2016

@author: waffleboy
"""

from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
import string
import gensim
from gensim import corpora
import pandas as pd


stop = set(stopwords.words('english'))
exclude = set(string.punctuation)
lemma = WordNetLemmatizer()


def clean(doc):
    stop_free = ' '.join([i for i in doc.lower().split() if i not in stop])
    punc_free = ''.join(ch for ch in stop_free if ch not in exclude)
    normalized = " ".join(lemma.lemmatize(word) for word in punc_free.split())
    return normalized
    
             
def run_lda(doc_clean,num_topics):
    dictionary = corpora.Dictionary(doc_clean)
    doc_term_matrix = [dictionary.doc2bow(doc) for doc in doc_clean]
    lda = gensim.models.ldamodel.LdaModel
    ldamodel = lda(doc_term_matrix,num_topics=num_topics,id2word = dictionary,passes = 60)
    return ldamodel

def pretty_print_results(ldamodel,num_topics,num_words):
    z = ldamodel.print_topics(num_topics=num_topics,num_words=num_words)
    group = 1
    for i in range(len(z)):
        entry = z[i][1]
        entry = ''.join([i for i in entry if not (i.isdigit() or i == '.' or i == '*')])
        entry = entry.replace('"','')
        entry = '{}. {}'.format(group,entry)
        entry = entry.replace(' + ',', ')
        z[i] = entry
        group += 1
    return z

    

df = pd.read_excel("/home/waffleboy/Desktop/NEA/data.xlsx")

cols_to_try = ["Title","Text"]
num_topics = 5

for col in cols_to_try:
    doc_complete = df[col]
    doc_complete = doc_complete.dropna()
    
    doc_clean = []
                 
    for i in doc_complete.index:
        doc = doc_complete[i]
        doc_clean.append(clean(doc).split())
    
    ldamodel  = run_lda(doc_clean,num_topics)
    results = pretty_print_results(ldamodel,num_topics,num_words = 7)
    for entry in results:
        print(entry)
    print('\n')
        