curl --silent "https://api.github.com/repos/mozilla/DeepSpeech/releases/latest" | 
    grep '"tag_name":' | 
    sed -E 's/.*"([^"]+)".*/\1/'