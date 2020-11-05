from pydub import AudioSegment
from math import ceil

def split(audiofile, segmentlength_mins): # length of each segment in mins
    # reference: https://stackoverflow.com/questions/37999150/how-to-split-a-wav-file-into-multiple-wav-files

    if '.wav' in str(audiofile):
        audio = AudioSegment.from_wav(audiofile)
    else:
        print('Error: Not .wav')
        return
    audioname = str(audiofile).split('/')[-1]
    print(audioname)
    export_folder = '/'.join(str(audiofile).split('/')[:-1])
    print('Export folder path: ', export_folder)
    durationmins = ceil(audio.duration_seconds / 60)
    segments = durationmins / segmentlength_mins
    print('Audio duration (mins): ',durationmins)
    print('No. of segments: ',segments)

    def singlesplit(audio, from_min, to_min, export_folder, export_name):
        t1 = from_min * 60 * 1000
        t2 = to_min * 60 * 1000
        split_audio = audio[t1:t2]
        split_audio.export(export_folder + '/' + export_name, format="wav")
    
    audio_segments = []
    for i in range(0, durationmins, segmentlength_mins):
        export_name = str(i) + '_' + audioname
        singlesplit(audio, i, i+segmentlength_mins, export_folder, export_name)
        print(str(i) + ' Done')
        audio_segments.append(export_folder + '/' + export_name)
        if i == durationmins - segmentlength_mins:
            print('Split complete.')
    
    print(audio_segments)
    return audio_segments

if __name__ == "__main__":
    testfile = 'file_io/goats.wav'
    split(testfile, 1) # test run success.