# Summarize Your Zoom Classes
*Because you're studious, not because you weren't there*

### In the Works:
1. Speech to text is slow as shit because it runs the downloaded video/audio in real time to do the transcription. Will need to splice up the media and run transcription on all the bits simultaneously to try to have the process finish in one human lifetime.
2. If recording already has Zoom's auto transcript, need to find a way to determine that, export the transcript and use it in place of the crap we're using now (see 3).
3. Speech to text is janky as hell, but most free libraries probably are. May consider creating a premium version and using something like Google's paid STT.
4. Make a quick function to create a credentials.ini for new users.

### Quickstart

1. **Record the Zoom audio** with something like the Chrome Audio Capture extension.
2. Dump the **.wav audio** into the ```file_io``` folder
3. **Run zoomsumm.py** with .wav's file name (with or without the extension '.wav'); in the terminal that's ```python3 zoomsumm.py filename```
4. You can also run zoomsumm.py without specifying a file name; there'll just be an extra step to confirm which file you want processed.
4. ZoomSumm will **transcribe the audio, punctuate the transcription and put it through NLP** to create the summary.
5. If it's the first time you're running this, it'll take a couple seconds to download the models required for transcription.
6. Finally, the script will **package** your .wav audio and all the files generated in the process into a **single folder** named after the audio.

### Reconfiguring defaults

You can reconfig the following if you'd like in the .config file.

- LANGUAGE: Language.
- SUMMLENGTH: Number of sentences the summary will contain.
- SUMMMETHOD: Method used by ```sumy``` to summarize. 1=Luhn, 2=Lex-Rank, 3=Text-Rank
- IOFOLDER: The folder where input .wav files and output .txt files will live.

### Transcribing the .wav

Audio files are first resampled using ```ffmpeg``` to 16kHz mono, because that's what's required for the next step. Resampled audio will be saved as filename_16.wav.

The resampled audio is then transcribed using ```Mozilla DeepSpeech```.

**Note: The transcription is usually the weak link** of this entire process due to poor audio quality and/or speech with accents.

The raw transcript will be saved as filename_16.txt.

### Punctuating and summarizing the transcript

The raw transcript is punctuated with ```punctuator2``` via POST request. The punctuate text is then saved as filename_16_punc.txt.

Punctuated text is pushed through ```sumy```, an NLP-based summarizer. Method used to summarize can be configured (refer above).

Summarized text will be saved as filename_16_punc_summ_method.txt.

For example, if the input file is are_goats_op.wav, the file output is are_goats_op_16_punc_summ_luhn.txt.

Convoluted, yes. But also unmistakeable.

Incidentally, I've left are_goats_op in the file_io folder as an example.

### If you already have a reliable, punctuated transcript

You can dump the prepared transcript as a .txt file in the file_io folder, just as you would a .wav file.

ZoomSumm will just skip the first few steps and get right to summarizing.