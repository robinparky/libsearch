import sys
import time
import glob, os
import sqlite3
import numpy as np
import pandas as pd
import copy
import os

import keras.backend as K
from keras.layers.convolutional import Conv1D
from keras.layers.core import Dense, Dropout, Masking
from keras.layers.recurrent import LSTM
from keras.layers.wrappers import Bidirectional, TimeDistributed
from keras.models import load_model as keras_load_model
from keras.models import Sequential


os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
BUFFERSIZE = 100000
MAX_LEN = 50

def nlf_encode(seq):
    x = pd.DataFrame([nlf[i] for i in seq]).reset_index(drop=True)
    #show_matrix(x)
    e = x.values.flatten()
    return e

def cosine_similarity(y_true, y_pred):
    length = K.int_shape(y_pred)[1]
    y_true = K.batch_flatten(y_true)
    y_pred = K.batch_flatten(y_pred)
    y_true = K.l2_normalize(y_true, axis=-1)
    y_pred = K.l2_normalize(y_pred, axis=-1)
    cos = K.sum(y_true * y_pred, axis=-1, keepdims=True)
    result = -K.repeat_elements(cos, rep=length, axis=1)
    return result

start = time.time()

"""
fileList = []
for i in range(1, len(sys.argv)):
    os.chdir(sys.argv[i])
    for fname in glob.glob("*.idx"):
        fileList.append(sys.argv[i] + fname)
        print(sys.argv[i] + fname)
"""

if len(sys.argv) != 3:
    print("Error with command line inputs")
    sys.exit(0)
else:
    MODEL_PATH = sys.argv[1]
    OUTPUT_PATH = sys.argv[2]

#fileList = ["/data/tyrande/data/1.txt" ,"/data/tyrande/data/3.txt" ]
fileList = ["/home/bernard/peptideList.txt"]

model = keras_load_model(MODEL_PATH)
nlf = pd.read_csv('../NLF.csv',index_col=0)

conn = sqlite3.connect(OUTPUT_PATH)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS predictions(Sequence TEXT,\
                                                  Protein_ID TEXT,\
                                                  Offset TEXT,\
                                                  Length TEXT,\
                                                  PrecursorMZ float,\
                                                  Retention_Time float,\
                                                  Charge integer,\
                                                  b1 TEXT,\
                                                  b2 TEXT,\
                                                  bn1 TEXT,\
                                                  bn2 TEXT,\
                                                  bo1 TEXT,\
                                                  bo2 TEXT,\
                                                  y1 TEXT,\
                                                  y2 TEXT,\
                                                  yn1 TEXT,\
                                                  yn2 TEXT,\
                                                  yo1 TEXT,\
                                                  yo2 TEXT\
                                                  )")
peptideList = []
itemArray = []
lineCounter = 0

#peptideSeqString, proteinId, offset, length

for fname in fileList:
    with open(fname) as f:
        for line in f:
            split = line.split()
            #print(split)
            sequence = split[0]
            proteinId = split[1]
            offset = split[2]
            length = split[3]

            peptideList.append(sequence)
            itemArray.append([proteinId, offset, length])

            lineCounter += 1

            if lineCounter % BUFFERSIZE == 0:

                npArray = []
                for i, pep in enumerate(peptideList):
                    original = pep;
                    if len(pep) >= MAX_LEN:
                        continue
                    while len(pep) < MAX_LEN:
                        pep =pep + "0"
                    try:
                        encodedPeptide = nlf_encode(pep)
                    except:
                        continue
                    npArray.append(encodedPeptide)

                npArray = np.array(npArray)
                npArray = np.reshape(npArray, (npArray.shape[0], 1, npArray.shape[1]))

                predictions = model.predict(npArray)

                ionList = ["b1", "b2", "bn1","bn2", "bo1", "bo2", "y1", "y2", "yn1", "yn2", "yo1", "yo2" ]

                for i in range(len(npArray)):
                    peptide = peptideList[i]

                    #Size of predictionArray split into the 12 sections
                    split = len(predictions[0]) / 12

                    #The size of the partition without padding.
                    splitEnd = len(peptideList[0]) - 1

                    ionObj = {}

                    splitCnt = 0
                    cnt = 0
                    while splitCnt <12:
                        done = False
                        ionArray = []
                        while True:
                            if done == False:
                                ionArray.append(str(predictions[i][cnt]))
                            cnt += 1
                            if cnt % split == 0:
                                break
                            elif cnt % split > splitEnd:
                                done = True
                        ionObj[ionList[splitCnt]] = ','.join(copy.copy(ionArray))
                        splitCnt += 1

                    c.execute("INSERT INTO predictions(Sequence, Protein_ID, Offset, Length,\
                                                       PrecursorMZ, Charge, Retention_Time,\
                                                       b1,b2,bn1,bn2,bo1,bo2,y1,y2,yn1,yn2,yo1,yo2)\
                                                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", \
                                                       (peptide, itemArray[0][0], itemArray[0][1],\
                                                       itemArray[0][2], 0, 2, 0, \
                                                       ionObj["b1"], ionObj["b2"],\
                                                       ionObj["bn1"], ionObj["bn2"],\
                                                       ionObj["bo1"], ionObj["bo2"],\
                                                       ionObj["y1"], ionObj["y2"],\
                                                       ionObj["yn1"], ionObj["yn2"],\
                                                       ionObj["yo1"], ionObj["yo2"]))
                    conn.commit()
                print(lineCounter)
                print("Done, Elapsed Time:", time.time() - start)
                sys.exit()

                if lineCounter > 25000:
                    print("Done, Elapsed Time:", time.time() - start)
                    sys.exit()

                peptideList = []
                itemArray = []

conn.close()
print("Done, Elapsed Time:", time.time() - start)
