from __future__ import division
import sys
import pickle
import time
import math

import gc



import tensorflow as tf
from tensorflow import keras
import numpy as np
import matplotlib.pyplot as plt

if len(sys.argv) != 5 :
    print(len(sys.argv))
    print("Error with command line inputs")
    sys.exit(0)
else:
    save = sys.argv[1]
    outputPath = sys.argv[2]
    batchSize = int(sys.argv[3])
    numEpochs = int(sys.argv[4])

start = time.time()

print("Running program")
print("Training Data with ", numEpochs, " epochs.")
print("\n")

'''--------------------------------------------------------------------------'''
print("Gathering Data from Files")
with tf.device('/cpu:0'):
    with open (save + 'spectrumsList', 'rb') as sp:
        spectrums = pickle.load(sp)
    sp.close()
    with open (save + 'labelList', 'rb') as lp:
        labelList = pickle.load(lp)
    sp.close()
    with open (save + 'indexList', 'rb') as lp:
        indexList = pickle.load(lp)
    sp.close()
    with open (save + 'idList', 'rb') as lp:
        idList = pickle.load(lp)
    sp.close()
    with open (save + 'binArray', 'rb') as lp:
        binArray = pickle.load(lp)
    sp.close()
    with open (save + 'outputLabels', 'rb') as lp:
        outputLabels = np.array(pickle.load(lp))
    sp.close()
'''--------------------------------------------------------------------------'''

print(binArray.shape)
def generator(batchSize):
    while True:
        for i in range(0, len(binArray), batchSize):
            print(indexList[i:i + batchSize])
            yield binArray[i:i + batchSize], indexList[i:i + batchSize]



#Metrics for printing(mostly)
inputs = len(spectrums)
totalBins = len(binArray[0])
inputLayers = len(binArray)
outputLayers = len(outputLabels)


print("Inputs (spectrums): ",inputs)
print("\tShapes: ", binArray.shape);
print("\tType: ", binArray.dtype);
print("\tInput Layers: ", inputLayers, "\n")

print("Outputs:", )
print("\tNum: ", outputLabels);
print("\tType: ", outputLabels.dtype);
print("\tOutput Layers: ", outputLayers)


"""from keras.backend.tensorflow_backend import set_session
config = tf.ConfigProto()
# dynamically grow GPU memory
config.gpu_options.allow_growth = True set_session(tf.Session(config=config))
"""

def create_model():
    inputShape = binArray.shape
    model = keras.Sequential()
    model.add(tf.keras.layers.Conv2D(filters=64, kernel_size=2, padding='same', activation='relu', input_shape=inputShape))
    model.add(tf.keras.layers.MaxPooling2D(pool_size=2))
    model.add(tf.keras.layers.Dropout(0.3))

    model.add(tf.keras.layers.Conv2D(filters=32, kernel_size=2, padding='same', activation='relu'))
    model.add(tf.keras.layers.MaxPooling2D(pool_size=2))
    model.add(tf.keras.layers.Dropout(0.3))

    model.add(tf.keras.layers.Flatten())
    model.add(tf.keras.layers.Dense(256, activation='relu'))
    model.add(tf.keras.layers.Dropout(0.5))
    model.add(tf.keras.layers.Dense(10, activation='softmax'))
    return baseModel



model  = create_model()
model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])
model.summary()
'''--------------------------------------------------------------------------'''

#Train the data

#model.fit_generator(generator(batchSize), steps_per_epoch = np.ceil(len(binArray)/batchSize), epochs = numEpochs)

model.fit(binArray, indexList, batch_size = batchSize, epochs = numEpochs)
#model.save_weights(outputPath)
model.save(outputPath)


print ("Finished Training")
train = time.time()
print ("Elapsed Time: " + str(round(train - start)) + "\n")