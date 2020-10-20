import ffmpeg, deepspeech, wave
import numpy as np
import requests, configparser, sys, os, shutil
from time import sleep
from getmodels import getmodels
from downdloadfile import rundownload

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
    print('Resampling audio...')
    audioIn = ffmpeg.input(input_file_path)
    output_file_path = str(input_file_path)[:-4] + '_16' + '.wav'
    print('Output path: ', output_file_path)
    audioOut = ffmpeg.output(audioIn, output_file_path, ar=16000, ac=1)
    ffmpeg.run(audioOut, overwrite_output=True)
    return output_file_path

def speechtotext(resampled_audio):
    print('Converting speech to text...')
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
    print('Punctuating transcript...')
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
    print('Summarizing transcript...')
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
    print('Packaging everything into a nice folder...')
    foldername = filename.split('/')[-1][:-4]
    newfolder = os.path.join('./file_io',foldername)
    os.mkdir(newfolder)
    # os.listdir()
    filesinIO = [f for f in os.listdir('./file_io') if os.path.isfile(os.path.join('./file_io', f))]
    projfiles = [p for p in filesinIO if foldername in p]
    print(projfiles)
    for i in projfiles:
        projectfile = os.path.join('./file_io',i)
        shutil.move(projectfile,os.path.join(newfolder,i))

def start_menu():
    useroption = input(''.join([
        '='*20+'\n',
        'What brings you here zoomer? Enter number below.\n',
        '1: Summarize a downloaded recording\n',
        '2: Download recording from URL and summarize (only NYU supported)\n',
        '3: Coming soon\n',
        'Q: Quit program\n',
        'Your call: '
        ])
    )
    if useroption == '1':
        filesinIO = [f for f in os.listdir('./file_io') if os.path.isfile(os.path.join('./file_io', f))]
        inputname = ''
        fileno = 0
        while inputname == '':
            if fileno >= len(filesinIO):
                print('No file chosen.')
                sleep(0.5)
                break
            checkwithuser = input('Work on {}? [Y/n] '.format(filesinIO[fileno]))
            if checkwithuser in ['Y','y']:
                inputname = IOFOLDER + str(filesinIO[fileno])
                break
            fileno += 1
        if not inputname == '':
            if '.wav' in inputname:
                output_wav = resample(inputname)
                trans = speechtotext(output_wav)
                punctuated = punctuate(trans)
                summarize(punctuated)
                package_into_folder(inputname)
            elif '.txt' in inputname:
                summarize(inputname)
                package_into_folder(inputname)
        else:
            print('No file found. Make sure your .mp4, .wav, or .txt is in the file_io folder.')
            sleep(1)
    elif useroption == '2':
        filename = IOFOLDER + rundownload()
        summarize(punctuate(speechtotext(resample(filename))))
        package_into_folder(filename)

    elif useroption == '3':
        return
    elif useroption in ['q','Q']:
        return
    start_menu()

def runshortcut(shortcut):
    if '.wav' in shortcut:
        inputname = IOFOLDER + shortcut # python3 zoomsumm.py filename
    else:
        inputname = IOFOLDER + shortcut + '.wav' # python3 zoomsumm.py filename
        
    if os.path.exists(inputname) == False:
        if os.path.exists(inputname[:-4] + '.txt') == False:
            print('File does not exist; Make sure your .mp4, .wav, or .txt is in the file_io folder.')
            sleep(1)
            print('Taking you to main menu.')
            sleep(1)
            start_menu()
        else:
            readytranscript = inputname[:-4] + '.txt'
            summarize(readytranscript)
            package_into_folder(readytranscript)
        
    else:
        output_wav = resample(inputname)
        trans = speechtotext(output_wav)
        punctuated = punctuate(trans)
        summarize(punctuated)
        package_into_folder(inputname)

if __name__ == "__main__":
    if not os.path.exists('.credentials.ini'):
        if input('Welcome to ZoomSumm mortal. Want to save your school/org login credentials for automatic Zoom cloud recording downloads? [y/n]\n') in ['Y','y']:
            print("JK we haven't coded in that function. Give us a sec.") # Follow up
        else:
            print('Cool. Taking you to main menu.')
            sleep(1)
    if len(sys.argv) == 2:
        runshortcut(sys.argv[1])
    elif len(sys.argv) > 2:
        print('Too many files man, chill out. One at a time.')
        sleep(1)
        print('Taking you to main menu.')
        sleep(1)
        start_menu()
    else:
        start_menu()
    
    """
        if '.wav' in sys.argv[1]:
            inputname = IOFOLDER + str(sys.argv[1]) # python3 zoomsumm.py filename
        else:
            inputname = IOFOLDER + str(sys.argv[1]) + '.wav' # python3 zoomsumm.py filename
        
        if os.path.exists(inputname) == False:
            if os.path.exists(inputname[:-4] + '.txt') == False:
                print('File does not exist. Try again.')
            else:
                readytranscript = inputname[:-4] + '.txt'
                summarize(readytranscript)
                package_into_folder(readytranscript)
        
        else:
            output_wav = resample(inputname)
            trans = speechtotext(output_wav)
            punctuated = punctuate(trans)
            summarize(punctuated)
            package_into_folder(inputname)
    """