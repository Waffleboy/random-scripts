#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 14:32:44 2016

@author: waffleboy
"""

import numpy as np
import pandas as pd
import nltk
import re
import os
import codecs
import matplotlib.pyplot as plt
import matplotlib as mlp
from sklearn.metrics import silhouette_score
from sklearn.manifold import MDS
from sklearn import feature_extraction
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from sklearn.cluster import KMeans
#import mpdl3

stopwords = nltk.corpus.stopwords.words('english')
stemmer = nltk.stem.PorterStemmer()
    
def tokenize_only(text):
    tokens = [word.lower() for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(text)]
    filtered_tokens = []
    for token in tokens:
        if re.search('[a-zA-Z]',token):
            filtered_tokens.append(token)
    return filtered_tokens

def tokenize_and_stem(text):
    tokens = tokenize_only(text)
    stems = [stemmer.stem(t) for t in tokens]
    return stems
    
total_vocab_stemmed = []
total_vocab_tokenized = []

#df = pd.read_excel("/home/waffleboy/Desktop/NEA/data.xlsx")
#text = df["Text"]
df = pd.read_csv("/home/waffleboy/Desktop/NEA/env_reddit_scraper/results/2016-11-09 to 2016-12-09.csv")
col = "title"

text = df[col]


for i in text:
    allwords_stemmed = tokenize_and_stem(i)
    total_vocab_stemmed.extend(allwords_stemmed)
    
    all_words_tokenized = tokenize_only(i)
    total_vocab_tokenized.extend(all_words_tokenized)

vocab_frame = pd.DataFrame({'words':total_vocab_tokenized},index = total_vocab_stemmed)
print("There are {} items in vocab_frame".format(vocab_frame.shape[0]))

# TF -IDF



#define vectorizer parameters
tfidf_vectorizer = TfidfVectorizer(max_df=0.8, max_features=200000,
                                 min_df=0.2, stop_words='english',
                                 use_idf=True, tokenizer=tokenize_and_stem, ngram_range=(1,3))

%time tfidf_matrix = tfidf_vectorizer.fit_transform(text) #fit the vectorizer to synopses
print(tfidf_matrix.shape)

terms = tfidf_vectorizer.get_feature_names()

#similarity between docs
dist = 1 - cosine_similarity(tfidf_matrix)

##mini experiment
#all_num_clusters = [12,13,14,15,16]
#num_clusters = 5
#
#for num_clusters in all_num_clusters:
#    km = KMeans(n_clusters=num_clusters)
#    km.fit(tfidf_matrix)
#    clusters = km.labels_.tolist()
#    print(silhouette_score(tfidf_matrix,clusters))

num_clusters = 2

km = KMeans(n_clusters=num_clusters)
km.fit(tfidf_matrix)
clusters = km.labels_.tolist()

#data = {'title':df["Title"],'text':df["Text"],'cluster':clusters}
#frame = pd.DataFrame(data, index = [clusters],columns = ['title','text','cluster'])

data = {'title':df["title"],'cluster':clusters}
frame = pd.DataFrame(data, index = [clusters],columns = ['title','cluster'])



#find clusters in each group
frame['cluster'].value_counts()


print("Top terms per cluster:")
print()
#sort cluster centers by proximity to centroid
order_centroids = km.cluster_centers_.argsort()[:, ::-1] 

lst = []

for i in range(num_clusters):
    print("Cluster %d words:" % i, end='')
    newlst = []
    for ind in order_centroids[i, :6]: #replace 6 with n words per cluster
        newlst.append(vocab_frame.ix[terms[ind].split(' ')].values.tolist()[0][0].encode('utf-8', 'ignore'))
        print(' %s' % vocab_frame.ix[terms[ind].split(' ')].values.tolist()[0][0].encode('utf-8', 'ignore'), end=',')
    lst.append(newlst)
    print() #add whitespace
    print() #add whitespace

#CONVERT TO 2D
MDS()

mds = MDS(n_components=2,dissimilarity="precomputed",random_state=1)
pos = mds.fit_transform(dist)
xs,ys = pos[:,0],pos[:,1]

def generate_random_color():
    import random
    r = lambda: random.randint(0,255)
    return '#%02X%02X%02X' % (r(),r(),r())


#cluster_colors = [generate_random_color() for x in range(len(lst))]
#cluster_colors = {k:v for k,v in enumerate(cluster_colors)}
cluster_colors = {0: '#1b9e77', 1: '#d95f02', 2: '#7570b3', 3: '#e7298a', 4: '#66a61e'}

#set up cluster names using a dict

cluster_names = {k:v for k,v in enumerate(lst)}
#
#cluster_names = {0: 'emissions, environmental, new',
#                 1: 'development, reduce, energy'}
#
#cluster_names = {0: '0 energy,development,reduce' ,
#                 1: '1 government, increases, new, environmental',
#                 2: '2 new, research, development, reduce',
#                 3: '3 reduce, emissions, government, years'}
#                 
#cluster_names = {0: 'development,government,environmental' ,
#                 1: 'energy, reduce',
#                 2: 'emissions, reduce, government',
#                 3: 'research development, increases', 
#                 4: 'environmental development'}

                 #some ipython magic to show the matplotlib plots inline
%matplotlib inline 

#create data frame that has the result of the MDS plus the cluster numbers and titles
df2 = pd.DataFrame(dict(x=xs, y=ys, label=clusters, title=data["title"])) 

#group by cluster
groups = df2.groupby('label')


# set up plot
fig, ax = plt.subplots(figsize=(17, 9)) # set size
ax.margins(0.05) # Optional, just adds 5% padding to the autoscaling

#iterate through groups to layer the plot
#note that I use the cluster_name and cluster_color dicts with the 'name' lookup to return the appropriate color/label
for name, group in groups:
    ax.plot(group.x, group.y, marker='o', linestyle='', ms=12, 
            label=cluster_names[name], color=cluster_colors[name], 
            mec='none')
    ax.set_aspect('auto')
    ax.tick_params(\
        axis= 'x',          # changes apply to the x-axis
        which='both',      # both major and minor ticks are affected
        bottom='off',      # ticks along the bottom edge are off
        top='off',         # ticks along the top edge are off
        labelbottom='off')
    ax.tick_params(\
        axis= 'y',         # changes apply to the y-axis
        which='both',      # both major and minor ticks are affected
        left='off',      # ticks along the bottom edge are off
        top='off',         # ticks along the top edge are off
        labelleft='off')
    
ax.legend(numpoints=1)  #show legend with only 1 point

#add label in x,y position with the label as the film title
for i in range(len(df2)):
    ax.text(df2.ix[i]['x'], df2.ix[i]['y'],'', size=8)  
    
plt.show() #show the plot


#
#writer = pd.ExcelWriter('clusters.xlsx',engine='xlsxwriter')
#df2.to_excel(writer)
#writer.save()
#

### D3JS VERSION ###

class TopToolbar(mpld3.plugins.PluginBase):
    def __init__(self):
        self.dict_ = {"type": "toptoolbar"}

df = pd.DataFrame(dict(x=xs, y=ys, label=clusters, title=titles)) 

#group by cluster
groups = df.groupby('label')

#define custom css to format the font and to remove the axis labeling
css = """
text.mpld3-text, div.mpld3-tooltip {
  font-family:Arial, Helvetica, sans-serif;
}

g.mpld3-xaxis, g.mpld3-yaxis {
display: none; }

svg.mpld3-figure {
margin-left: -200px;}
"""

# Plot 
fig, ax = plt.subplots(figsize=(14,6)) #set plot size
ax.margins(0.03) # Optional, just adds 5% padding to the autoscaling

#iterate through groups to layer the plot
#note that I use the cluster_name and cluster_color dicts with the 'name' lookup to return the appropriate color/label
for name, group in groups:
    points = ax.plot(group.x, group.y, marker='o', linestyle='', ms=18, 
                     label=cluster_names[name], mec='none', 
                     color=cluster_colors[name])
    ax.set_aspect('auto')
    labels = [i for i in group.title]
    
    #set tooltip using points, labels and the already defined 'css'
    tooltip = mpld3.plugins.PointHTMLTooltip(points[0], labels,
                                       voffset=10, hoffset=10, css=css)
    #connect tooltip to fig
    mpld3.plugins.connect(fig, tooltip, TopToolbar())    
    
    #set tick marks as blank
    ax.axes.get_xaxis().set_ticks([])
    ax.axes.get_yaxis().set_ticks([])
    
    #set axis as blank
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)

    
ax.legend(numpoints=1) #show legend with only one dot

mpld3.display() #show the plot



## LDA

import string
def strip_proppers(text):
    # first tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
    tokens = [word for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent) if word.islower()]
    return "".join([" "+i if not i.startswith("'") and i not in string.punctuation else i for i in tokens]).strip()
    

#strip any proper nouns (NNP) or plural proper nouns (NNPS) from a text
from nltk.tag import pos_tag

def strip_proppers_POS(text):
    tagged = pos_tag(text.split()) #use NLTK's part of speech tagger
    non_propernouns = [word for word,pos in tagged if pos != 'NNP' and pos != 'NNPS']
    return non_propernouns
    
from gensim import corpora, models, similarities 

#remove proper names
preprocess = [strip_proppers(doc) for doc in text]

#tokenize
tokenized_text = [tokenize_only(text) for text in preprocess]

#remove stop words
texts = [[word for word in text if word not in stopwords] for text in tokenized_text]

dictionary = corpora.Dictionary(texts)

#remove extremes (similar to the min/max df step used when creating the tf-idf matrix)
dictionary.filter_extremes(no_below=1, no_above=0.8)

#convert the dictionary to a bag of words corpus for reference
corpus = [dictionary.doc2bow(text) for text in texts]
          
lda = models.LdaModel(corpus, num_topics=num_clusters, 
                            id2word=dictionary, 
                            update_every=5, 
                            chunksize=10000, 
                            passes=100)


topics_matrix = lda.show_topics(formatted=False, num_words=20)

for entry in topics_matrix:
    index = entry[0]
    words = entry[1]
    words.sort(key = lambda x:x[1],reverse=True)
    word = [x[0] for x in words]
    print(index,word[:5])
#    
#0 ['research', 'studi', 'water', 'use', 'found']
#1 ['wast', 'energi', 'use', 'recycl', 'solar']
#2 ['emiss', 'carbon', 'energi', 'climat', 'would']
#3 ['pollut', 'air', 'vehicl', 'car', 'citi']