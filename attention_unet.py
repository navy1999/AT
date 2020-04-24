# -*- coding: utf-8 -*-
"""Attention-Unet

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1AZPXcx2zFwhCU1au6mS8_yq6_FfZxWlA
"""

import os
import sys
import random
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from tqdm import tqdm
from itertools import chain
from skimage.io import imread, imshow, imread_collection, concatenate_images
from skimage.transform import resize
from skimage.morphology import label
from PIL import ImageFile
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Input
from tensorflow.keras.layers import Dropout, Lambda
from tensorflow.keras.layers import Conv2D, Conv2DTranspose, BatchNormalization
from tensorflow.keras.layers import MaxPooling2D
from tensorflow.keras.layers import concatenate, Activation,add,multiply
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras import backend as K
import tensorflow as tf

IMG_WIDTH = 512
IMG_HEIGHT = 512
IMG_CHANNELS = 3
warnings.filterwarnings('ignore', category=UserWarning, module='skimage')
seed = 42
random.seed = seed
np.random.seed = seed

!unzip Multi_Organ

import cv2
import os

def load_images_from_folder(folder):
    images = []
    for filename in os.listdir(folder):
        img = cv2.imread(os.path.join(folder,filename))
        if img is not None:
            images.append(img)
    return images
test_data=load_images_from_folder('data_dir/Test/data')
test_labels=load_images_from_folder('data_dir/Test/labels')
train_data=load_images_from_folder('data_dir/Train/data')
train_labels=load_images_from_folder('data_dir/Train/labels')
val_data=load_images_from_folder('data_dir/Val/data')
val_labels=load_images_from_folder('data_dir/Val/labels')

X_train = np.zeros((100, IMG_HEIGHT, IMG_WIDTH, IMG_CHANNELS), dtype=np.uint8)
Y_train = np.zeros((100, IMG_HEIGHT, IMG_WIDTH, 1), dtype=np.bool)
print('Getting and resizing train images and masks ... ')

X_train=np.array(train_data)
X_labels=np.array(train_labels)

Y_train.shape

mask = np.zeros((IMG_HEIGHT, IMG_WIDTH, 1), dtype=np.bool)

X_labels=X_labels[:,:,:,0]

X_labels=X_labels.reshape((len(X_labels),512,512,1))

X_labels.shape

for i in range(100):
  Y_train[i]=np.maximum(mask,X_labels[i])

Y_train.shape

import matplotlib.pyplot as plt

plt.imshow(np.squeeze(Y_train[0]))

X_test=np.array(test_data)

X_test.shape

ix = random.randint(0, 100)
imshow(X_train[ix])
plt.show()
imshow(np.squeeze(Y_train[ix]))
plt.show()

def attention_block_2d(x, g, inter_channel, data_format='channels_last'):
    theta_x = Conv2D(inter_channel, [1, 1], strides=[1, 1], data_format=data_format)(x)
    phi_g = Conv2D(inter_channel, [1, 1], strides=[1, 1], data_format=data_format)(g)
    f = Activation('relu')(add([theta_x, phi_g]))
    psi_f = Conv2D(1, [1, 1], strides=[1, 1], data_format=data_format)(f)
    rate = Activation('sigmoid')(psi_f)
    att_x = multiply([x, rate])

    return att_x

# U-Net model with attention gates
inputs = Input((IMG_HEIGHT, IMG_WIDTH, IMG_CHANNELS))
s = Lambda(lambda x: x / 255) (inputs)

c1 = Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same') (s) #512
c1 = BatchNormalization()(c1)
c1 = Dropout(0.1) (c1)
c1 = Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same') (c1)
c1 = BatchNormalization()(c1)
p1 = MaxPooling2D((2, 2)) (c1)

c2 = Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same') (p1)
c2 = BatchNormalization()(c2)
c2 = Dropout(0.1) (c2)
c2 = Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same') (c2)
c2 = BatchNormalization()(c2)
p2 = MaxPooling2D((2, 2)) (c2)

c3 = Conv2D(128, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same') (p2)
c3 = BatchNormalization()(c3)
c3 = Dropout(0.2) (c3)
c3 = Conv2D(128, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same') (c3)
c3 = BatchNormalization()(c3)
p3 = MaxPooling2D((2, 2)) (c3)

c4 = Conv2D(256, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same') (p3)
c4 = BatchNormalization()(c4)
c4 = Dropout(0.2) (c4)
c4 = Conv2D(256, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same') (c4)
c4 = BatchNormalization()(c4)
p4 = MaxPooling2D(pool_size=(2, 2)) (c4)

c5 = Conv2D(512, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same') (p4)
c5 = BatchNormalization()(c5)
c5 = Dropout(0.3) (c5)
c5 = Conv2D(512, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same') (c5)
c5 = BatchNormalization()(c5)

u6 = Conv2DTranspose(128, (2, 2), strides=(2, 2), padding='same') (c5)
in_channel = c5.get_shape().as_list()[3]
c4 = attention_block_2d(x=c4, g=u6 ,inter_channel=in_channel // 4, data_format='channels_last')
u6 = concatenate([u6, c4])
c6 = Conv2D(256, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same') (u6)
c6 = BatchNormalization()(c6)
c6 = Dropout(0.2) (c6)
c6 = Conv2D(256, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same') (c6)
c6 = BatchNormalization()(c6)

u7 = Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same') (c6)
in_channel = c5.get_shape().as_list()[3]
c3 = attention_block_2d(x=c3, g=u7,inter_channel=in_channel // 4, data_format='channels_last')
u7 = concatenate([u7, c3])
c7 = Conv2D(128, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same') (u7)
c7 = BatchNormalization()(c7)
c7 = Dropout(0.2) (c7)
c7 = Conv2D(128, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same') (c7)
c7 = BatchNormalization()(c7)

u8 = Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same') (c7)
in_channel = c5.get_shape().as_list()[3]
c2 = attention_block_2d(x=c2, g=u8,inter_channel=in_channel // 4, data_format='channels_last')
u8 = concatenate([u8, c2])
c8 = Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same') (u8)
c8 = BatchNormalization()(c8)
c8 = Dropout(0.1) (c8)
c8 = Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same') (c8)
c8 = BatchNormalization()(c8)

u9 = Conv2DTranspose(16, (2, 2), strides=(2, 2), padding='same') (c8)
in_channel = c5.get_shape().as_list()[3]
c1 = attention_block_2d(x=c1, g=u9,inter_channel=in_channel // 4, data_format='channels_last')
u9 = concatenate([u9, c1], axis=3)
c9 = Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same') (u9)
c9 = BatchNormalization()(c9)
c9 = Dropout(0.1) (c9)
c9 = Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same') (c9)
c9 = BatchNormalization()(c9)

outputs = Conv2D(1, (1, 1), activation='sigmoid') (c9)

model = Model(inputs=[inputs], outputs=[outputs])
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
model.summary()

results = model.fit(X_train, Y_train, validation_split=0.1, batch_size=5, epochs=100)

sizes_test = []
for i in range(5):
  sizes_test.append([512,512])

preds_train = model.predict(X_train[:int(X_train.shape[0]*0.9)], verbose=1)
preds_val = model.predict(X_train[int(X_train.shape[0]*0.9):], verbose=1)
preds_test = model.predict(X_test, verbose=1)
preds_train_t = (preds_train > 0.5).astype(np.uint8)
preds_val_t = (preds_val > 0.5).astype(np.uint8)
preds_test_t = (preds_test > 0.5).astype(np.uint8)
preds_test_upsampled = []
for i in range(len(preds_test_t)):
    preds_test_upsampled.append(resize(np.squeeze(preds_test_t[i]), 
                                       (sizes_test[i][0], sizes_test[i][1]), 
                                       mode='constant', preserve_range=True))

ix = random.randint(0, len(preds_val_t))
imshow(X_train[int(X_train.shape[0]*0.9):][ix])
plt.show()
imshow(np.squeeze(Y_train[int(Y_train.shape[0]*0.9):][ix]))
plt.show()
imshow(np.squeeze(preds_val_t[ix]))
plt.show()

model.save_weights("att_unet.hdf5")

model.save_weights("att_u_net.h5")

model.save("att_unet_navneet.h5")

model.save("att_unet_vvr.hdf5")

model=load_model('att_unet_navneet.h5')

test_data=np.array(test_data)
test_data.shape

test_labels=np.array(test_labels)
test_labels=test_labels[:,:,:,0]
test_labels.shape

test_labels=test_labels.reshape((5,512,512,1))

preds_test_t.shape

plt.imshow(np.squeeze(preds_test_t[0]))

from sklearn.metrics import confusion_matrix  
import numpy as np

def compute_iou(y_pred, y_true):
    # ytrue, ypred is a flatten vector
    y_pred = y_pred.flatten()
    y_true = y_true.flatten()
    current = confusion_matrix(y_true, y_pred, labels=[0, 1])
    # compute mean iou
    intersection = np.diag(current)
    ground_truth_set = current.sum(axis=1)
    predicted_set = current.sum(axis=0)
    union = ground_truth_set + predicted_set - intersection
    IoU = intersection / union.astype(np.float32)
    return np.mean(IoU)

io=compute_iou(preds_test_t,test_labels)

io

from sklearn import metrics

def precision_recall(y_pred,y_true):
  y_pred=y_pred.flatten()
  y_true=y_true.flatten()
  recall=metrics.recall_score(y_true,y_pred,average='micro')
  precision=metrics.precision_score(y_true,y_pred,average='micro')
  f1=metrics.f1_score(y_true,y_pred,average='micro')
  return recall,precision,f1

r,p,f1=precision_recall(preds_test_t,test_labels)

print(test_labels.shape)
print(preds_test_t.shape)

print(r,p,f1)

v=test_labels[0,:,:,:]
np.count_nonzero(test_labels[0,:,:,:])

a=test_labels.reshape((5,512,512)).astype(np.bool).flatten()
b=preds_test_t.reshape((5,512,512)).astype(np.bool).flatten()

y=np.sum(a)
w=np.sum(b)
z=np.size(a)-np.sum(a)
y+z

np.sum(a==True)

tp_tn=np.sum(a==b)

fp_fn=np.sum(a!=b)

tp_tn+fp_fn

i=(a==True)
j=(b==True)
tp=np.sum(i==j)
tn=tp_tn-tp
tn

tp_tn