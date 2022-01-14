# SpotifyWaveApp

This app is done with h2o.ai Wave app. 

Firstly, user stream history must be download from Spotify account. Then uploading of the stream history data to the app will create data visualisations and show the result analysis. 


## Running this App Locally

### System Requirements

1. Python 3.6+
2. pip3

### 1. Run the Wave Server

You can easily use [the documentation](https://wave.h2o.ai/docs/installation) and set up the Wave Server on your local machine. 

Once the server is up and running you can easily use any Wave app.

### 2. Setup Your Python Environment

in Windows. You can create virtual environments with other tools too.
```bash
git clone https://github.com/semihdesticioglu/SpotifyWaveApp
cd SpotifyWaveApp
conda create --name h2o_wave
activate h2o_wave
pip install -r requirements.txt
```

### 3. Run the App

```bash
 wave run spotify_app
```

### 4. View the App

Point your favorite web browser to [localhost:10101/spotify](http://localhost:10101/spotify)

![alt text](screenshots/Capture.PNG)
