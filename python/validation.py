import tensorflow as tf
import tensorflow_io as tfio
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, Dense, Flatten, Dropout, MaxPooling2D
import os
from datetime import datetime
import numpy as np
from matplotlib import pyplot as plt


def load_model(path):
    model = tf.keras.models.load_model(path)
    model.compile('Adam', loss='BinaryCrossentropy', metrics=[tf.keras.metrics.Recall(),tf.keras.metrics.Precision()])
    return model


def validate_model(model, test):
    model.evaluate(test)


# load file, squeeze stereo to mono and resample to 16kHz
def load_wav_16k_mono(filename):
    # Load encoded wav file
    file_contents = tf.io.read_file(filename)
    # Decode wav (tensors by channels)
    wav, sample_rate = tf.audio.decode_wav(file_contents, desired_channels=1)
    # Removes trailing axis
    wav = tf.squeeze(wav, axis=-1)
    sample_rate = tf.cast(sample_rate, dtype=tf.int64)
    # Goes from 44100Hz to 16000hz - amplitude of the audio signal
    wav = tfio.audio.resample(wav, rate_in=sample_rate, rate_out=16000)
    return wav


# Lädt Datei als mono wav mit 16khz
# Erstellt einen Stack, sliced datei in vorgesehene slice-size und packt slices in stack
def pre_process(file_path, label, rnd_val, aug = False):
    wav = load_wav_16k_mono(file_path)
    audio_slice = wav[0:1600]

    if aug:
      aug_seed = 999
      tf.random.set_seed = aug_seed
      # random slice based on rnd_val
      audio_0 = int(rnd_val % tf.shape(wav)[0])
      # when starting point does not leave 1600 samples, go back so it does
      audio_slice = wav[audio_0:audio_0+1600]

    zero_padding_size = tf.zeros([1600] - tf.shape(audio_slice)[0], dtype=tf.float32)
    audio_slice = tf.concat([zero_padding_size, audio_slice],0)

    spectrogram = tf.signal.stft(audio_slice, frame_length=320, frame_step=32)
    spectrogram = tf.abs(spectrogram)
    spectrogram = tf.expand_dims(spectrogram, axis=2)
    return spectrogram, label


# uses recursion to get into deepest dir and collect all wav files
def dataset_dir_scalper(path):
  dataset = None
  for file in os.listdir(path):
    filename = os.fsencode(file)
    if os.path.isdir(path+file+"/"):
      if dataset is not None and not dataset == []:
        try:
          dataset = dataset.concatenate(dataset_dir_scalper(path+file+"/"))
        except:
          print("Filepath: "+str(path+file)+" has no .wav entries")
      else:
        dataset = dataset_dir_scalper(path+file+"/")

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


def batch_map_data(data, pre_proc_method, batchSize, aug=False):
  rnd_val = tf.random.uniform(minval=0, maxval=1000000, shape=[1], seed = 9999, dtype = tf.int32).numpy()[0]
  data = data.map(lambda ds, label:  pre_proc_method(ds, label, rnd_val, aug) )
  data = data.cache()
  data = data.shuffle(buffer_size=17268)
  data = data.batch(batchSize, num_parallel_calls=tf.data.AUTOTUNE)
  data = data.prefetch(2)
  return data

def get_train_test(data):
  train = data.take(int(len(data)*.9))
  test = data.skip(int(len(data)*.9)).take(int(len(data)*.1))
  return train, test

# Create neural network
def create_1f_cnn(train):
  # get input shape
  samples, labels = train.as_numpy_iterator().next()
  input_shape = samples.shape[1:]

  # Using relu to avoid 'dead' neurons (everthing < 0 )
  model = Sequential()
  model.add(Conv2D(32, (3,3), activation='relu', input_shape=input_shape))
  model.add(Conv2D(64, (3,3), activation='relu'))
  model.add(MaxPooling2D((2,2)))  
  model.add(Dropout(.2))
  model.add(Flatten())
  model.add(Dense(128, activation='relu'))
  model.add(Dense(1, activation='sigmoid'))

  model.compile('Adam', loss='BinaryCrossentropy', metrics=[tf.keras.metrics.Recall(),tf.keras.metrics.Precision()])

  model.summary()

  return model

# model version and auto save path
# save mechanism specs
# train model
def train_model(model, train, test, epochs):
  auto_save_base_path = "/content/gdrive/MyDrive/DL/DeepSheeps/announcement_detection/models/auto_saving/"
  auto_save_path = auto_save_base_path + "/" + str(datetime.now()) + "/model.ckpt"
  cp_callback = tf.keras.callbacks.ModelCheckpoint(auto_save_path, save_weights_only=True, verbose=1)

  hist = model.fit(train, epochs=epochs, validation_data=test)

  return model, hist

# helsfyr2 with 9 dbfs dataset
pos_path = "../data/helsfyr2_with_9_dbfs/pos/"
neg_path = "../data/helsfyr2_with_9_dbfs/neg/"


## Data pipeline
# Load data from path and slice it into desired length
data = create_dataset(pos_path, neg_path)
data = batch_map_data(data, pre_process, 64, True)

train, test = get_train_test(data)

# Prepare model
model = create_1f_cnn(train)
model, hist = train_model(model, train, test, 30)

# load and show history of training model
"""
history = np.load("../web_app/model/model_1/history.npy", allow_pickle=True)
print(history.item().keys())
plt.plot(history.item()["val_loss"])
plt.plot(history.item()["loss"])
plt.show()

history = np.load("../web_app/model/model_2_dropout/history.npy", allow_pickle=True)
print(history.item().keys())
plt.plot(history.item()["val_loss"])
plt.plot(history.item()["loss"])
plt.show()

history = np.load("../web_app/model/model_2_1_higher_dropout/history.npy", allow_pickle=True)
print(history.item().keys())
plt.plot(history.item()["val_loss"])
plt.plot(history.item()["loss"])
plt.show()

history = np.load("../web_app/model/model_3_fewer_layer_MaxPooling/history.npy", allow_pickle=True)
print(history.item().keys())
plt.plot(history.item()["val_loss"])
plt.plot(history.item()["loss"])
plt.show()

# Prepare model
#model = create_cnn(train)
#model, hist = train_model(model, train, test, 30)

#model = load_model("../web_app/model/model_3_fewer_layer_MaxPooling/model.h5")
#validate_model(model, test)

#validate_model(model, test)"""
