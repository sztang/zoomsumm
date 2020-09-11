import wget
import subprocess
import requests
import os

def getmodels():
    ver = subprocess.run(['sh', './models/findlatest.sh'],stdout=subprocess.PIPE).stdout.decode('utf-8')
    ver = ver.replace("\n", "")
    print(ver)
    pbmm = 'https://github.com/mozilla/DeepSpeech/releases/download/{}/deepspeech-{}-models.pbmm'.format(ver,ver[1:])
    scorer = 'https://github.com/mozilla/DeepSpeech/releases/download/{}/deepspeech-{}-models.scorer'.format(ver,ver[1:])
    print(pbmm)

    # pbmm_path = requests.get(pbmm)
    # with open('/model/model.pbmm', 'w') as p:
    #     p.write(pbmm_path.content)
    # scorer_path = requests.get(scorer)
    # with open('/model/scorer.scorer', 'w') as f:
    #     f.write(scorer_path.content)
    # ppath = os.path.join()
    pbmm2 = pbmm.split('/')[-1].split('-')[-1]
    scorer2 = scorer.split('/')[-1].split('-')[-1]
    print(pbmm2,scorer2)

    wget.download(pbmm,os.path.join('./models',pbmm2))
    wget.download(scorer,os.path.join('./models',scorer2))