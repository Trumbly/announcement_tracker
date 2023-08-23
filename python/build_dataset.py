# we should have a reproducible script to create the train / dev / test split
# we need to test if the dev and test sets should come from the same distribution

# The best and most secure way to split the data into these three sets is to have one directory for train, one for dev and one for test.


## create the split into train, dev and test

# use a fixed seed so that every call to python build_dataset.py will result in the same output.

# e.g.
# filenames = ['img_000.jpg', 'img_001.jpg', ...]
# filenames.sort()  # make sure that the filenames have a fixed order before shuffling
# random.seed(230)
# random.shuffle(filenames) # shuffles the ordering of filenames (deterministic given the chosen seed)
#
# split_1 = int(0.8 * len(filenames))
# split_2 = int(0.9 * len(filenames))
# train_filenames = filenames[:split_1]
# dev_filenames = filenames[split_1:split_2]
# test_filenames = filenames[split_2:]

#from pyannote.audio import Model

import os
from pydub import AudioSegment, silence
import random

## method for data augmentation
## can generate the max. possible size for a dataset based on the size of pos and neg
## data
## saves data in an other dir to prevent massive ram usage

#
# def data_aug(pos_path, neg_path):
#   p_dir = os.fsencode(pos_path)
#   n_dir = os.fsencode(neg_path)
#
#   p_len = len(p_dir)
#   n_len = len(n_dir)
#   max_combs = p_len * n_len
#
#   print(max_combs)
#
#   for i, _ in enumerate(p_dir):
#     taken_rd_nums = []
#     curr_rd_num = -1
#     #overlay_file = None
#     while curr_rd_num not in taken_rd_nums: #and not overlay_file.endswith(".wav"):
#       curr_rd_num = int(random.uniform(0, n_len))
#       print("Found number: " + str(curr_rd_num))
#       if curr_rd_num not in taken_rd_nums:
#         taken_rd_nums.append(curr_rd_num)
#       overlay_file = n_dir[curr_rd_num]
#
#     print("Proceeding with this number and file")
#
#     neg_file = AudioSegment.from_wav(neg_path)
#     pos_file = AudioSegment.from_wav(pos_path)
#
#     overlay = pos_file.overlay(neg_file, position=0)
#     os.mkdir(pos_path + "overlays/")
#     overlay.export(
#       pos_path + "overlays/" + "overlay_" + str(i) + "_" + "_with_" + str(p_dir[int(i)]) + ".wav",
#       format="wav")

# 1. data augmentation with pos and neg files to overlay
# no data augmentation at this point, the given helsfyr2 files
# already contain a good amount of noise
# maybe more for finetuning
#data_aug("/Users/annikaschilk/Documents/techlabs/gong_ber/", "/Users/annikaschilk/Documents/techlabs/")



# Create positive files
# Add gong sound to negative files in different positions - shift by 100ms
# Save file

import os

# https://stackoverflow.com/questions/60918209/pydub-overlay-delay
# https://snyk.io/advisor/python/pydub/functions/pydub.AudioSegment
# https://stackoverflow.com/questions/4039158/mixing-two-audio-files-together-with-python


def create_pos_dataset(path):
    directory_neg = os.fsencode(path)
    filename_gong = AudioSegment.from_wav(path + '/gong_ber/1-EW8678-n-Heraklion_Boarding-beginnt_de,en_2022_goodquality.wav')
    pos = 0
    for file in os.listdir(directory_neg):
        # the position parameter means where on the original sound do you wish to start.
        filename_neg = os.fsdecode(file)
        if filename_neg.endswith(".wav") and pos < 5000:
            print("Filename negative: " + filename_neg)
            print("Filename Gong: 1-EW8678-n-Heraklion_Boarding-beginnt_de,en_2022_goodquality.wav")


            print("Position of gong start: ", pos)
            file_neg = AudioSegment.from_wav(path + filename_neg)
            filename_pos_with_ambient = file_neg.overlay(filename_gong, position=pos)

            #os.mkdir(path + "overlays/")
            filename_pos_with_ambient.export(path + "overlays/" + filename_neg + "_" + str(pos) + '_filename_gong.wav', format="wav")

            pos += 100

        elif filename_neg.endswith(".wav") and pos == 5000:
            pos = 0




#create_pos_dataset("/Users/annikaschilk/Documents/techlabs/")

#print(len(os.listdir("/Users/annikaschilk/Documents/techlabs/")))


import tensorflow as tf


# uses recursion to get into deepest dir and collect all wav files
def dataset_dir_scalper(path):
  dataset = None
  for file in os.listdir(path):
    filename = os.fsencode(file)
    if os.path.isdir(path):
      if dataset is not None and not dataset == []:
        try:
          dataset = dataset.concatenate(dataset_dir_scalper(path+file))
        except:
          print("Filepath: "+str(path+file)+" has no .wav entries")
      else:
        dataset = dataset_dir_scalper(path+file)

  if dataset is not None:
    try:
      return dataset.concatenate(tf.data.Dataset.list_files(path+'*.wav'))
    except:
      return dataset
  else:
    try:
      return tf.data.Dataset.list_files(path+'*.wav')
    except:
      return []

def create_dataset(pos_path, neg_path):
  neg = dataset_dir_scalper(neg_path)
  pos = dataset_dir_scalper(pos_path)

  # labels
  positives = tf.data.Dataset.zip((pos, tf.data.Dataset.from_tensor_slices(tf.ones(len(pos)))))
  negatives = tf.data.Dataset.zip((neg, tf.data.Dataset.from_tensor_slices(tf.zeros(len(neg)))))

  print("Pos ds len: "+str(positives.cardinality().numpy()))
  print("Neg ds len: "+str(negatives.cardinality().numpy()))


  # combine positive and negative tensors
  data = positives.concatenate(negatives)
  return data


pos_path = "/Users/annikaschilk/Documents/techlabs/overlays/"
neg_path = "/Users/annikaschilk/Documents/techlabs/"

#create_dataset(pos_path, neg_path)

dataset = tf.data.Dataset.list_files('*.wav')
dataset = dataset.map(lambda x: x + 1)
