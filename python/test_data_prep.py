import os
from pydub import AudioSegment, silence
import random
from matplotlib import pyplot as plt

def mp3_to_wav(path, filename):
  print(path+filename)
  mp3 = AudioSegment.from_mp3(path+filename)
  exp_filename = filename[:-3] + "wav"
  mp3.export(path + exp_filename, format="wav")
  os.remove(path + filename)

def m4a_to_wav(path, filename):
  mp3 = AudioSegment.from_file(path+filename)
  exp_filename = filename[:-3] + "wav"
  print(exp_filename)
  mp3.export(path + exp_filename, format="wav")

#TODO not tested, add to allToWave
#TODO why not one function using AudioSegment.from_file for all audio formats?
def webm_to_wav(path, filename):
  webm = AudioSegment.from_file(path+filename)
  exp_filename = os.path.splitext(filename)[0] + ".wav"
  print(filename)
  webm.export(path, exp_filename, format="wav")

def allToWav(path):
  directory = os.fsencode(path)
  replace_path = path+"old_files/";
  for file in os.listdir(directory):
      filename = os.fsdecode(file)
      if filename.endswith(".mp3"):
          mp3_to_wav(path, filename)
          if not os.path.exists(replace_path):
            os.mkdir(replace_path)
          os.replace(path+filename, replace_path+filename)
      elif filename.endswith(".m4a"):
        m4a_to_wav(path, filename)
        if not os.path.exists(replace_path):
            os.mkdir(replace_path)
        os.replace(path+filename, replace_path+filename)
        


# Slices many announcements with a short silent pause in one audio file to many files
#https://stackoverflow.com/questions/40896370/detecting-the-index-of-silence-from-a-given-audio-file-using-python
def slice_many_to_one(path, filename):
  audio = AudioSegment.from_wav(path + filename)
  slice_count = 0
  if audio.duration_seconds > 5:
    sil = silence.detect_nonsilent(audio, min_silence_len=50, silence_thresh=-40)
    sil = [((start/1000),(stop/1000)) for start,stop in sil] #convert to sec

    print(sil)

    for i, a in enumerate(sil):
      x,y = a
      if y-x > 1:
        #silence_duration = (4999-(y-x)*1000)/2
        #silence_segment = AudioSegment.silent(duration=silence_duration, frame_rate=audio.frame_rate)
        new_file=audio[x*1000 : y*1000]
        #new_file= silence_segment + new_file + silence_segment
        if(y-x>5):
          new_file.export(path + filename + "_" + "slice" + "-" + str(i) +"_slice_manually.wav", format="wav")
          slice_count=+1
        else:
          new_file.export(path + filename + "_" + "slice" + "-" + str(i) +".wav", format="wav")
          slice_count=+1
      else:
        print("The generated slice is too small and won't be exported!")
  else:
    print("The given positive audio file "+filename+" is too short to be sliced!")

  if slice_count > 0:
    return True
  else:
    return False

## slices an audio file into the desired slice size
def create_slices(path, filename, sice_size):
  print(path+filename)
  audio = AudioSegment.from_file(path + filename)
  slice_count = 0
  fn_wo_ed = filename[:-4]
  print("Audio size: "+ str(audio.duration_seconds))
  if audio.duration_seconds > sice_size:
    slice_0 = 0
    slice_1 = sice_size
    while slice_1 < audio.duration_seconds:
      audio_slice = audio[slice_0*1000:slice_1*1000]
      audio = audio[slice_1*1000:]
      print("Saving to: " + path+fn_wo_ed+"_slice_"+str(slice_count+1)+".wav")
      audio_slice.export(path+fn_wo_ed+"_slice_"+str(slice_count+1)+".wav",format="wav")
      slice_count+=1
  else:
    print("The given negative audio file "+fn_wo_ed+" is too short to be sliced!")

  if slice_count > 0:
    return True
  else:
    return False

## slices all .wav files in an directory into the desired slice size
def slice_dir(path, slice_size):
  directory = os.fsencode(path)
  replace_path = path+"sliced_source_files/"
  for file in os.listdir(directory):
      filename = os.fsdecode(file)
      if filename.endswith(".wav"):
        create_slices(path, filename, slice_size)
        if not os.path.exists(replace_path):
            os.mkdir(replace_path)
        os.replace(path+filename, replace_path+filename)


## data pipeline to prepare data for our model
def test_data_prep(path, slice_size):
  # 1: Slicing into 100ms
  slice_dir(path, slice_size)

## method for data augmentation
## can generate the max. possible size for a dataset based on the size of pos and neg
## data
## saves data in an other dir to prevent massive ram usage
def data_aug(pos_path, neg_path):
  p_dir = os.fsencode(pos_path)
  n_dir = os.fsencode(neg_path)

  p_len = len(p_dir)
  n_len = len(n_dir)
  max_combs = p_len * n_len

  print(max_combs)

  for i,_ in enumerate(p_dir):
    taken_rd_nums = []
    curr_rd_num = -1
    overlay_file = None
    while curr_rd_num not in taken_rd_nums and not overlay_file.endswith(".wav"):
      curr_rd_num = int(random.uniform(0, n_len))
      print("Found number: "+curr_rd_num)
      if curr_rd_num not in taken_rd_nums:
        taken_rd_nums.append(curr_rd_num)
      overlay_file = n_dir[curr_rd_num]

    print("Proceeding with this number and file")

    neg_file = AudioSegment.from_wav(neg_path+n_dir[int(curr_rd_num)])
    pos_file = AudioSegment.from_wav(pos_path+p_dir[int(i)])

    overlay = pos_file.overlay(neg_file, position=0)
    os.mkdir(pos_path+"overlays/")
    overlay.export(pos_path + "overlays/" + "overlay_" + str(i)+ "_" + n_dir[int(curr_rd_num)] + "_with_" + p_dir[int(i)] + ".wav", format="wav")

## Delete silence in audio file based on rel volumne differences in frames
# --> silence_tresh=audio.dBFS - X
def del_sil(file):
  filename = os.fsdecode(file)
  audio = AudioSegment.from_wav(filename)
  sil = silence.detect_nonsilent(audio, min_silence_len=50, silence_thresh=audio.dBFS-9)
  print("dBFS: "+str(audio.dBFS))
  print("Silence: "+str(sil))
  audio_r = None
  for r in sil:
    if audio_r is None:
      audio_r = audio[r[0]:r[1]]
    else:
      audio_r +=audio[r[0]:r[1]]
  audio_r.export(file[:-4]+"_tf.wav")

# delete silence in all files of path
def def_sil_all(path_to_dir):
  directory = os.fsencode(path_to_dir)
  replace_path = path_to_dir+"with_silence/"
  for file in os.listdir(directory):
      filename = os.fsdecode(file)
      if filename.endswith(".wav"):
        del_sil(path_to_dir+filename)
        if not os.path.exists(replace_path):
          os.mkdir(replace_path)
        os.replace(path_to_dir+filename, replace_path+filename)


# 1. data augmentation with pos and neg files to overlay
# no data augmentation at this point, the given helsfyr2 files
# already contain a good amount of noise
# maybe more for finetuning
#data_aug(pos_path, neg_path):

# 2. detect and delete all silence sequences in files 
# files with silence are placed inside "with_silence" dir 
# the processed ones stay inside the given one
def_sil_all("data/en_ds_v1/")

# 3. create 100ms slices, save them in the current dir
# place input files in "sliced_soure_files"
test_data_prep("data/en_ds_v1/", 0.100)