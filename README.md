# labear

A project to learn some deep learning... 

Code is based on this article: https://towardsdatascience.com/audio-deep-learning-made-simple-sound-classification-step-by-step-cebc936bbe5 

Links to dataset and metadata can be found in the article. The dataset/metadata will be expanded upon with sounds from home/labs/etc. We should find a place to store this which we can both access. For recordings I've used the app Voice Recorder (V 3.19) which records .wav format to my phone. 

## Structure of data directory 
The `appliances` directory is structured in such a way that the label of each sound is defined by the parent directory. 

```
data
├── appliances
│   ├── dehumidifier
│   ├── gas_boiler
│   └── lesker_system
└── urbansound8k
    ├── UrbanSound8K.csv
    ├── fold1
    ├── fold10
    ├── fold2
    ├── fold3
    ├── fold4
    ├── fold5
    ├── fold6
    ├── fold7
    ├── fold8
    └── fold9
```