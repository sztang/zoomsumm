import ffmpeg
import deepspeech
import wave
import numpy as np
import requests
import configparser
import sys
import os
import shutil
from getmodels import getmodels

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.nlp.stemmers import Stemmer
from sumy.summarizers.luhn import LuhnSummarizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.utils import get_stop_words

config = configparser.ConfigParser()
config.read('.config')
LANGUAGE = config['DEFAULT']['LANGUAGE']
SENTENCES_COUNT = int(config['DEFAULT']['SUMMLENGTH'])
IOFOLDER = config['DEFAULT']['IOFOLDER']
if os.path.exists('./models/model.pbmm') == False:
    getmodels()

def resample(input_file_path):
    audioIn = ffmpeg.input(input_file_path)
    output_file_path = str(input_file_path)[:-4] + '_16' + '.wav'
    print('Output path: ', output_file_path)
    audioOut = ffmpeg.output(audioIn, output_file_path, ar=16000, ac=1)
    ffmpeg.run(audioOut, overwrite_output=True)
    return output_file_path

def speechtotext(resampled_audio):
    w = wave.open(resampled_audio, 'r')
    frames = w.getnframes()
    buffer = w.readframes(frames)
    data16 = np.frombuffer(buffer, dtype=np.int16)

    model = deepspeech.Model('models/model.pbmm')
    transcript = model.stt(data16)
    model.enableExternalScorer('models/scorer.scorer')
    transcript_file_path = str(resampled_audio)[:-4] + '.txt'
    with open(transcript_file_path, 'a') as f:
        f.write(transcript)
        print(transcript)
    return transcript_file_path

def punctuate(transcript):
    url = 'http://bark.phon.ioc.ee/punctuator'
    f = open(transcript,'r')
    payload = dict(text=f.read())
    print('Transcript text: ',f.read())
    res = requests.post(url, data=payload)
    transcript_punc = str(transcript)[:-4] + '_punc' + '.txt'
    with open(transcript_punc, 'a') as f2:
        f2.write(res.text)
    return transcript_punc

def summarize(final_transcript, askuser=False):
    parser = PlaintextParser.from_file(final_transcript, Tokenizer(LANGUAGE))
    stemmer = Stemmer(LANGUAGE)
    if askuser == True:
        summtype = input('Summarizer type? [1: Luhn, 2: Lex-Rank, 3: Text-Rank] ')
    else:
        summtype = config['DEFAULT']['SUMMMETHOD']
    
    if summtype == '1':
        summarizer = LuhnSummarizer(stemmer)
        typename = 'luhn'
    elif summtype == '2':
        summarizer = LexRankSummarizer(stemmer)
        typename = 'lex'
    elif summtype == '3':
        summarizer = TextRankSummarizer(stemmer)
        typename = 'tex'
    
    summarizer.stop_words = get_stop_words(LANGUAGE)
    count = SENTENCES_COUNT
    summaryfile = str(final_transcript)[:-4] + '_summ_' + typename + '.txt'
    for sentence in summarizer(parser.document, SENTENCES_COUNT):
        sentence_out = str(SENTENCES_COUNT - count + 1) + ':\n' + str(sentence) + '\n--------------\n'
        with open(summaryfile, 'a') as f:
            f.write(sentence_out)
        print(sentence_out)
        count -= 1
    return summaryfile

def package_into_folder(filename):
    foldername = filename.split('/')[-1][:-4]
    newfolder = os.path.join('./file_io',foldername)
    os.mkdir(newfolder)
    os.listdir()
    filesinIO = [f for f in os.listdir('./file_io') if os.path.isfile(os.path.join('./file_io', f))]
    projfiles = [p for p in filesinIO if foldername in p]
    print(projfiles)
    for i in projfiles:
        projectfile = os.path.join('./file_io',i)
        shutil.move(projectfile,os.path.join(newfolder,i))

if __name__ == "__main__":
    if '.wav' in sys.argv[1]:
        inputname = IOFOLDER + str(sys.argv[1]) # python3 zoomsumm.py filename
    else:
        inputname = IOFOLDER + str(sys.argv[1]) + '.wav' # python3 zoomsumm.py filename
    output_wav = resample(inputname)
    trans = speechtotext(output_wav)
    punctuated = punctuate(trans)
    summarize(punctuated)
    package_into_folder(inputname)