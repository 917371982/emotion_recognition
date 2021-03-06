# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 13:52:20 2019

@author: ress
"""

import os, glob
import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
import spec_augment_tensorflow 
from keras import models, layers
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
import pylab
from AudioDataGenerator import AudioDataGenerator

def amplitude(time, data):
    plt.figure(1)
    plt.subplot(211)
    plt.plot(time, data, linewidth=0.02, alpha=1, color='#000000')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.show()

#path_x = "D:/DB_audio/"
path_x = "D:/raw/"
rate = []
epochs = 10
batch_size = 16
num_of_files = 0
count = 0
num_of_augs = 1
max_shape = 0

filenames = glob.glob(os.path.join(path_x, '*/*.wav'))
folders = glob.glob(os.path.join(path_x, '*/'))
num_of_class = len(folders)

print (folders)

num_of_files = len(filenames)
num_of_files = num_of_files * (num_of_augs + 1)

labels = np.empty(num_of_files, dtype=object)
labels_arr = np.zeros((num_of_files, num_of_class))

for filename in filenames:
    X, sample_rate = librosa.load(filename)
    melspec = librosa.feature.melspectrogram(y=X, sr=sample_rate, n_mels=256, hop_length=128, fmax=8000) 
    shape = melspec.shape[0]*melspec.shape[1]
    if shape > max_shape: 
        max_shape = shape
        
x_train = np.zeros( (num_of_files, max_shape + 20) )

for filename in filenames:
    start = filename.find('\\', 0, len(filename)) + 1
    end = filename.find('\\', start, len(filename))

    X, sample_rate = librosa.load(filename)
    save_path = 'test.jpg'

    pylab.axis('off') # no axis
    pylab.axes([0., 0., 1., 1.], frameon=False, xticks=[], yticks=[]) # Remove the white edge
    melspec = librosa.feature.melspectrogram(y=X,
                                             sr=sample_rate,
                                             n_mels=256,
                                             hop_length=128,
                                             fmax=8000)
        
    shape = melspec.shape[0]*melspec.shape[1]
    print(len(x_train), melspec.shape, shape)
    
    labels[count] = filename[start:end]
    
    count = count + 1
    
    for i in range(num_of_augs):
        labels[count] = filename[start:end]
        
        warped_masked_spectrogram = spec_augment_tensorflow.spec_augment(mel_spectrogram=melspec)
        #print(warped_masked_spectrogram)
        #spec_augment_tensorflow.visualization_spectrogram(melspec, 'before')
        #spec_augment_tensorflow.visualization_spectrogram(warped_masked_spectrogram, 'after')
        
        warped_masked_spectrogram = warped_masked_spectrogram.reshape(shape)
        for j in range(shape):
            x_train[count][j] = warped_masked_spectrogram[j]
        count = count + 1
        
        librosa.display.specshow(librosa.power_to_db(melspec, ref=np.max))
        pylab.savefig(save_path, bbox_inches=None, pad_inches=0)
        pylab.close()
        
    melspec = melspec.reshape(shape)
    for j in range (shape):
        x_train[count - num_of_augs-1][j] = melspec[j]
        
x_train = x_train.reshape(num_of_files, max_shape + 20, 1)

labelencoder = LabelEncoder()
labels_arr = labelencoder.fit_transform(labels)
labels_arr = labels_arr.reshape(-1, 1) 
onehotencoder = OneHotEncoder()
labels_arr = onehotencoder.fit_transform(labels_arr).toarray()
labels_arr_end = np.zeros((num_of_files, 1))
for i in range (labels_arr.shape[0]):
    for j in range (labels_arr.shape[1]):
        if labels_arr[i][j] == 1:
            labels_arr_end[i] = j

datagen = AudioDataGenerator(
                featurewise_center=True,
                featurewise_std_normalization=True,
                shift=.2,
                horizontal_flip=True,
                zca_whitening=True)

input_shape = (max_shape + 20, 1)
model = models.Sequential()
model.add(layers.LSTM(16, activation='relu', input_shape=input_shape))
model.add(layers.Dense(16, activation='relu', input_shape=input_shape))
model.add(layers.Dense(num_of_class, activation='softmax'))

model.compile(optimizer='rmsprop',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

model.fit_generator(datagen.flow(x_train, labels_arr_end, batch_size=batch_size),
                    steps_per_epoch = num_of_files/batch_size,
                    epochs = epochs)