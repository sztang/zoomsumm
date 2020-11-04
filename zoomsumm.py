import ffmpeg, deepspeech, wave
import numpy as np
from math import ceil
import requests, configparser, sys, os, shutil
from time import sleep
from getmodels import getmodels
from downloadfile import rundownload
from splitaudio import split

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
        # print(transcript)
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
    # print(projfiles)
    for i in projfiles:
        projectfile = os.path.join('./file_io',i)
        shutil.move(projectfile,os.path.join(newfolder,i))

def segmented_transcribe(audiofile, autosegment=True):
    segmentlength_mins = 2
    if autosegment:
        from pydub import AudioSegment
        audio_duration = AudioSegment.from_wav(audiofile).duration_seconds / 60
        segmentlength_mins = ceil(audio_duration / 4)

        # below: tried large numbers of segments but didn't seem to improve time taken; make work better to keep segments to 4
        # if audio_duration > 60: # if audio is longer than 1h, divide it up into 15 segments
        #     segmentlength_mins = audio_duration / 15
        # elif audio_duration < 10: # if audio is very short, divide it into 2min segments
        #     segmentlength_mins = 3

    audio_segments = split(audiofile, segmentlength_mins)
    segments = len(audio_segments)

    """
    # Concurrent transcription method 1: bash background functions
    bashcommand = ''
    current_segment = 0
    for i in audio_segments:
        current_segment += 1
        if not current_segment == segments: # if not last segment
            bashsegment = 'python3 zoomsumm.py speechtotext {} & '.format(i)
        else:
            bashsegment = 'python3 zoomsumm.py speechtotext {}'.format(i)
        bashcommand += bashsegment
    print('Bash command: ',bashcommand)
    import subprocess
    subprocess.run(bashcommand, shell=True)
    """

    print('Transcribing {} segments - this should take about {} mins.'.format(segments,segmentlength_mins))
    from datetime import datetime
    starttime = datetime.now()

    # Concurrent transcription method 2: multiprocessing
    from multiprocessing import Pool
    with Pool(processes=segments) as pool:
        txt_files = pool.map(speechtotext, audio_segments)
    pool.close()
    pool.join()

    print('Segments have been transcribed.')
    timetaken = (datetime.now() - starttime).total_seconds()/60
    print('Time taken to transcribe: ',timetaken)
    output_folder = os.path.dirname(audiofile) # output combined transcript in same folder
    # output_folder = '/'.join(audiofile.split('/')[:-1])
    fulltxt_name = os.path.splitext(audiofile)[0] + '.txt'

    """
    # Combining method 1: bash
    bash_combinetxt = 'cd {}; cat *.txt > {}'.format(output_folder, fulltxt_name.split('/')[-1])
    subprocess.run(bash_combinetxt, shell = True)
    # issue: unsure if the order of concat is always correct
    """

    # Combining method 2: iterate over list
    # txt_files = [f for f in os.listdir(output_folder) if '.txt' in f]
    for t in sorted(txt_files):
        with open(t) as t:
            content = t.read()
        with open(fulltxt_name, 'a+') as f:
            f.write(content)
            f.write(' ')
        t.close()
    f.close()
    
    print('Segment transcripts have been combined into one.')

    # Delete redundant files
    redundant = [os.path.splitext(r.split('/')[-1])[0] for r in txt_files]
    for i in os.listdir(output_folder):
        # print(i)
        for r in redundant:
            # print(r)
            if r in i and os.path.isfile(os.path.join(output_folder,i)):
                os.remove(os.path.join(output_folder, i))
                print('Removed: ',i)
    print('Redundant segment files removed.')
    return fulltxt_name

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
                # trans = speechtotext(output_wav)
                trans = segmented_transcribe(output_wav)
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
        # trans = speechtotext(output_wav)
        trans = segmented_transcribe(output_wav)
        punctuated = punctuate(trans)
        summarize(punctuated)
        package_into_folder(inputname)

if __name__ == "__main__":
    
    if not os.path.exists('credentials.ini'):
        if input('Welcome to ZoomSumm, mortal. Want to save your school/org login credentials for automatic Zoom cloud recording downloads? [y/n]\n') in ['Y','y']:
            print("JK we haven't coded in that function. Give us a sec.") # Follow up
        else:
            print('Cool. Taking you to main menu.')
            sleep(1)
    if len(sys.argv) == 3 and sys.argv[1] == 'speechtotext': # direct call for transcribe with audio file provided in arg 2
        speechtotext(sys.argv[2])
    elif len(sys.argv) == 2: # call for full process run with audio file given in arg 1
        runshortcut(sys.argv[1])
    elif len(sys.argv) > 2: # call for full process run but with multiple audio files given
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