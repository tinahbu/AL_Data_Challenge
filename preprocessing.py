import numpy as np
import pickle # cPickle not available in Python 3
from collections import defaultdict
import sys, re
import pandas as pd
from gensim.models import KeyedVectors

def build_pos_neg_data(path_to_file, filename):
    '''
    From training file get positive examples and negative examples.
    '''
    file = path_to_file + filename
    all_data = pd.read_csv(file)
    pos = all_data[all_data['DETRACTOR'] == 1]
    neg = all_data[all_data['DETRACTOR'] == 0]
    return pos, neg

def build_data_cv(data_folder, cv = 10, clean_string = True):
    '''
    Load data and split them into 10 folds for cross validation.
    '''
    revs = []
    pos_file = data_folder[0]
    neg_file = data_folder[1]
    vocab = defaultdict(float)
    
    # Positive examples
    with open(pos_file, "rb") as f:
        for line in f:
            rev = []
            line = str(line, 'utf-8')
            rev.append(line.strip())
            if clean_string:
                orig_rev = clean_str(" ".join(rev))
            else:
                orig_rev = " ".join(rev).lower()
            words = set(orig_rev.split())
            for word in words:
                vocab[word] += 1
            # here y = 0 means positive
            datum  = {"y": 1,
                      "text": orig_rev,
                      "num_words": len(orig_rev.split()),
                      "split": np.random.randint(0, cv)}
            revs.append(datum)
            
    # Negative examples
    with open(neg_file, "rb") as f:
        for line in f:
            rev = []
            line = str(line, 'utf-8')
            rev.append(line.strip())
            if clean_string:
                orig_rev = clean_str(" ".join(rev))
            else:
                orig_rev = " ".join(rev).lower()
            words = set(orig_rev.split())
            for word in words:
                vocab[word] += 1
            # here y = 1 means negative
            datum  = {"y": 0,
                      "text": orig_rev,
                      "num_words": len(orig_rev.split()),
                      "split": np.random.randint(0,cv)}
            revs.append(datum)
    return revs, vocab

def get_W(word_vecs, k=300):
    """
    Get word matrix. W[i] is the vector for word indexed by i
    """
    vocab_size = len(word_vecs)
    word_idx_map = dict()
    W = np.zeros(shape=(vocab_size+1, k), dtype='float32')
    W[0] = np.zeros(k, dtype='float32')
    i = 1
    for word in word_vecs:
        W[i] = word_vecs[word]
        word_idx_map[word] = i
        i += 1
    return W, word_idx_map

def load_bin_vec(fname, vocab):
    """
    Loads 300x1 word vecs from Google (Mikolov) word2vec
    """
    word_vecs = {}
    with open(fname, "rb") as f:
        header = f.readline()
        vocab_size, layer1_size = map(int, header.split())
        binary_len = np.dtype('float32').itemsize * layer1_size
        for line in range(vocab_size):
            word = []
            while True:
                ch = f.read(1)
                if ch == ' ':
                    word = ''.join(word)
                    break
                if ch != '\n':
                    word.append(ch)
            if word in vocab:
                word_vecs[word] = np.fromstring(f.read(binary_len), dtype='float32')
            else:
                f.read(binary_len)
    return word_vecs

# def load_bin_vec(fname, vocab):
#     # Load pretrained model (since intermediate data is not included, the model cannot be refined with additional data)
#     model = Word2Vec.load_word2vec_format(fname, binary=True)
#     return model

def add_unknown_words(word_vecs, vocab, min_df=1, k=300):
    """
    For words that occur in at least min_df documents, create a separate word vector.
    0.25 is chosen so the unknown vectors have (approximately) same variance as pre-trained ones
    """
    for word in vocab:
        if word not in word_vecs and vocab[word] >= min_df:
            word_vecs[word] = np.random.uniform(-0.25,0.25,k)

def clean_str(string, TREC=False):
    """
    Tokenization/string cleaning for all datasets except for SST.
    Every dataset is lower cased except for TREC
    """
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
    string = re.sub(r"\'s", " \'s", string)
    string = re.sub(r"\'ve", " \'ve", string)
    string = re.sub(r"n\'t", " n\'t", string)
    string = re.sub(r"\'re", " \'re", string)
    string = re.sub(r"\'d", " \'d", string)
    string = re.sub(r"\'ll", " \'ll", string)
    string = re.sub(r",", " , ", string)
    string = re.sub(r"!", " ! ", string)
    string = re.sub(r"\(", " \( ", string)
    string = re.sub(r"\)", " \) ", string)
    string = re.sub(r"\?", " \? ", string)
    string = re.sub(r"\s{2,}", " ", string)
    return string.strip() if TREC else string.strip().lower()

def clean_str_sst(string):
    """
    Tokenization/string cleaning for the SST dataset
    """
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
    string = re.sub(r"\s{2,}", " ", string)
    return string.strip().lower()

if __name__=="__main__":
    
    w2v_file = sys.argv[1]
    # w2v_file = 'GoogleNews-vectors-negative300.bin'
    path_to_file = '/Users/tina.bu/Documents/Data_Challenge/Data/'
    filename = 'train.csv'
    data_folder = ["./Data/pos.txt",
                   "./Data/neg.txt"]
    
    print("-loading data...")
    print("--Spliting positive & negative examples")
    pos, neg = build_pos_neg_data(path_to_file, filename)
    print("--Saving positie & negatie examples in separate files")
    pos['verbatim'].to_csv(r'./Data/pos.txt', header=None, index=None, sep=' ', mode='a')
    neg['verbatim'].to_csv(r'./Data/neg.txt', header=None, index=None, sep=' ', mode='a')
    print("--Building cross validation set")
    revs, vocab = build_data_cv(data_folder, cv=10, clean_string=True)
    max_l = np.max(pd.DataFrame(revs)["num_words"])
    print("--data loaded!")
    print("---number of sentences: " + str(len(revs)))
    print("---vocab size: " + str(len(vocab)))
    print("---max sentence length: " + str(max_l))
    
    print("-loading word2vec vectors...")
    w2v = load_bin_vec(w2v_file, vocab)
    print("--word2vec loaded!")
    print =("--num words already in word2vec: " + str(len(w2v)))
    add_unknown_words(w2v, vocab)
    W, word_idx_map = get_W(w2v)
    rand_vecs = {}
    add_unknown_words(rand_vecs, vocab)
    W2, _ = get_W(rand_vecs)
    cPickle.dump([revs, W, W2, word_idx_map, vocab], open("mr.p", "wb"))
    print("-dataset created!")