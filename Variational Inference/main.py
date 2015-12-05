import sys
import os.path
sys.path.append(os.path.join('..', 'util'))

import set_compiler
set_compiler.install()

import pyximport
pyximport.install()

import numpy as np
import lda_vi_serial
import lda_vi_cython
import time
import matplotlib.pyplot as plt
from scipy.sparse import csc_matrix


if __name__ == '__main__':
    # N = 100
    # num_threads = 4
    # a = np.ones((N, N))
    # b = np.ones((N, N))
    # temp = np.ones(N)
    # start = time.time()
    # temp = lda_vi_cython.parallel_test(temp, num_threads)
    # duration = time.time() - start
    # for t in temp:
    #     print t, ' ',
    # print 'time is %s s' % duration


    corpus_ap = True

    if corpus_ap:
        # ### AP dtm
        # Read the vocabulary
        vocabulary = np.loadtxt('../ap/vocab.txt', dtype=str)
        V = len(vocabulary)

        # Read the data
        # Output format is a list of document (dtm) with
        # document: array([[index1, count1], ... , [index2, count2]])

        # To build the sparse matrix
        counts = []
        row_ind = []
        col_ind = []

        with open('../ap/ap.dat', 'r') as f:
            for i, row in enumerate(f):
                # row format is:
                #    [M] [term_1]:[count] [term_2]:[count] ...  [term_N]:[count]
                row_raw = row.split(' ')
                M = int(row_raw[0])
                document = np.zeros((M, 2))

                row_ind += M*[i]
                for j, w in enumerate(row_raw[1:]):
                    document[j, :] = [int(u) for u in w.split(':')]
                counts += list(document[:, 1])
                col_ind += list(document[:, 0])

        # dtm size
        C = i + 1

        # Building the dtm matrix
        dtm = csc_matrix((counts, (row_ind, col_ind)), shape=(C, V))
        dtm = dtm.toarray().astype(int)
    else:
        #  ### HARD: Artificial dtm
        # 100 docs
        # 450 words
        # 9 artificial topics (for each bag of 5 words)
        N_docs = 100
        N_words = 450
        num_topics = 9
        dtm = np.zeros((N_docs, N_words), dtype=int)  # shape (docs, words)
        vocabulary = np.arange(N_words)

        block = 10 * np.ones((20, 50), dtype=int)
        for i in range(num_topics):
            dtm[10*i:10*(i+2), 50*i:50*(i+1)] = block

    # #### Parameters
    S = 50
    max_iter = 100
    tau = 500
    kappa = 0.9
    alpha = 0.001
    eta = 0.001
    threshold = 0.00000001
    num_threads = 4
    ntopic = 10
    ndoc, nvoc = dtm.shape

    # ### Opt
    np.random.seed(0)
    # Initialization
    lambda_opt = np.random.gamma(100., 1./100., (ntopic, nvoc))
    gamma_opt = np.ones((ndoc, ntopic))
    lambda_int = np.zeros((ntopic, nvoc))
    phi = np.zeros((ntopic, nvoc))
    ExpLogTethad = np.zeros(ntopic)
    ExpELogBeta = np.zeros((ntopic, nvoc))
    time1 = time.time()
    # lda_batch makes in place operations
    lda_vi_cython.lda_batch(dtm, ntopic, S, num_threads, 512, 0.7, lambda_opt, gamma_opt, lambda_int, phi, ExpLogTethad, ExpELogBeta)

    time1_stop = time.time() - time1
    print 'Opt Time is', time1_stop, ' s'

    # ### Serial

    np.random.seed(0)
    lambda_ = np.random.gamma(100., 1./100., (ntopic, nvoc))
    time2 = time.time()
    lambda_serial, gamma_serial = lda_vi_serial.lda_batch(lambda_, dtm, ntopic, S, 512, 0.7)
    time2_stop = time.time() - time2
    print 'Serial Time is', time2_stop, ' s'

    if corpus_ap:
        # dtm AP: printing the result
        print 'Cython topics'
        topic_word = lambda_opt  # model.components_ also works
        n_top_words = 10
        for i, topic_dist in enumerate(topic_word):
            topic_words = np.array(vocabulary)[np.argsort(topic_dist)][:-(n_top_words+1):-1]
            print(u'Topic {}: {}'.format(i, ' '.join(topic_words)))

        print 'Serial topics'
        topic_word = lambda_serial  # model.components_ also works
        n_top_words = 10
        for i, topic_dist in enumerate(topic_word):
            topic_words = np.array(vocabulary)[np.argsort(topic_dist)][:-(n_top_words+1):-1]
            print(u'Topic {}: {}'.format(i, ' '.join(topic_words)))

    else:
        # Checking result

        plt.figure(1)
        # Cython
        plt.subplot(211)
        for i in xrange(num_topics):
            plt.plot(np.arange(N_words), lambda_opt[i, :])
        plt.title('Opt')
        # Serial
        plt.subplot(212)
        for i in xrange(num_topics):
            plt.plot(np.arange(N_words), lambda_serial[i, :])
        plt.title('Serial')
        plt.show()

    # raw_input()
    # for i in xrange(num_topics):
    #     plt.plot(np.arange(N_words), lambda_batch[i, :])
    #     plt.title('Batch')
    #     plt.show()
    #     raw_input()

    # raw_input()
    # for i in xrange(num_topics):
    #     plt.plot(np.arange(N_words), model.topic_word_[i, :])
    #     plt.title('Lda package')
    #     plt.show()
    #     raw_input()