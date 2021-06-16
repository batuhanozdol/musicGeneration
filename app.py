from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import numpy
import pandas as pd
import matplotlib.pyplot as plt
import os

#import numpy as np
#from numpy import core
#from numpy.core import _multiarray_umath

import glob
import pickle
import numpy
from music21 import converter, instrument, stream, note, chord
from keras.models import Sequential
from keras.layers import Dense, Dropout, LSTM, Activation, Bidirectional, Flatten, BatchNormalization, GRU
#from keras.utils import np_utils
from keras import utils
from keras.callbacks import ModelCheckpoint
from keras_self_attention import SeqSelfAttention

app = Flask(__name__)
app.secret_key = "musicGenerationusingAI"

FLASK_DEBUG=1
app.config['TEMPLATES_AUTO_RELOAD'] = True

transactions = []
POSTGRESQL_URI = "postgres://azstxybh:U-bQhxnQduXwuJIOe-X50a6bwqqiHOZh@rogue.db.elephantsql.com:5432/azstxybh"

connection = psycopg2.connect(POSTGRESQL_URI)

def generate_mozart(dataset, architect, note_length):
    """ Generate a piano midi file """
    #load the notes used to train the model
    with open('./static/mozart_data/notes', 'rb') as filepath:
        notes = pickle.load(filepath)

    # Get all pitch names
    pitchnames = sorted(set(item for item in notes))
    # Get all pitch names
    n_vocab = len(set(notes))

    network_input, normalized_input = prepare_sequences_output(notes, pitchnames, n_vocab)

    model = None
    
    if architect == "lstm":
        model = lstm_network(normalized_input, n_vocab)
    elif architect == "gru":
        model = gru_network(normalized_input, n_vocab)
    elif architect == "lstmatt":
       model = lstm_attention(normalized_input, n_vocab)
    elif architect == "bilstmatt":
       model = bilstm_attention(normalized_input, n_vocab)
    elif architect == "lstmattlstm":
       model = lstm_attention_lstm(normalized_input, n_vocab)
    elif architect == "bilstmattlstm":
       model = bilstm_attention_lstm(normalized_input, n_vocab)
    elif architect == "bilstmattgru":
       model = bilstm_attention_gru(normalized_input, n_vocab)
    elif architect == "bilstmattbigru":
       model = bilstm_attention_bigru(normalized_input, n_vocab)
    elif architect == "lstmlstmlstm":
       model = lstm_lstm_lstm_network(normalized_input, n_vocab)
    elif architect == "lstmbilstmbilstm":
       model = lstm_bilstm_bilstm_network(normalized_input, n_vocab)

    if model != None:
        prediction_output = generate_notes(model, network_input, pitchnames, n_vocab, note_length)
        create_midi(prediction_output)
    
def prepare_sequences_output(notes, pitchnames, n_vocab):
    """ Prepare the sequences used by the Neural Network """
    # map between notes and integers and back
    note_to_int = dict((note, number) for number, note in enumerate(pitchnames))

    sequence_length = 100
    network_input = []
    output = []
    for i in range(0, len(notes) - sequence_length, 1):
        sequence_in = notes[i:i + sequence_length]
        sequence_out = notes[i + sequence_length]
        network_input.append([note_to_int[char] for char in sequence_in])
        output.append(note_to_int[sequence_out])

    n_patterns = len(network_input)

    # reshape the input into a format compatible with LSTM layers
    normalized_input = numpy.reshape(network_input, (n_patterns, sequence_length, 1))
    # normalize input
    normalized_input = normalized_input / float(n_vocab)

    return (network_input, normalized_input)

def generate_notes(model, network_input, pitchnames, n_vocab, note_length):
    """ Generate notes from the neural network based on a sequence of notes """
    # pick a random sequence from the input as a starting point for the prediction
    start = numpy.random.randint(0, len(network_input)-1)

    int_to_note = dict((number, note) for number, note in enumerate(pitchnames))

    pattern = network_input[start]
    prediction_output = []

    # generate 500 notes
    for note_index in range(note_length):
        prediction_input = numpy.reshape(pattern, (1, len(pattern), 1))
        prediction_input = prediction_input / float(n_vocab)

        prediction = model.predict(prediction_input, verbose=0)

        index = numpy.argmax(prediction)
        result = int_to_note[index]
        prediction_output.append(result)

        pattern.append(index)
        pattern = pattern[1:len(pattern)]

    return prediction_output

def bilstm_attention(network_input, n_vocab):
    """ create the structure of the neural network """
    model = Sequential()    
    model.add(Bidirectional(LSTM(
    512, return_sequences=True),input_shape=(network_input.shape[1], network_input.shape[2]))) #n_time_steps, n_features? Needed input_shape in first layer, which is Bid not LSTM
    model.add(SeqSelfAttention(attention_activation='sigmoid'))
    model.add(Dropout(0.3))
    model.add(Flatten()) #Supposedly needed to fix stuff before dense layers
    
    model.add(Dense(n_vocab))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='rmsprop')

    # Load the weights to each node
    model.load_weights('static/weights/weights-Bilstmatt-40-1.1404-bigger.hdf5')
    
    return model

def bilstm_attention_gru(network_input, n_vocab):
    """ create the structure of the neural network """
    model = Sequential()

    model.add(Bidirectional(LSTM(512,return_sequences=True),input_shape=(network_input.shape[1], network_input.shape[2]))) #n_time_steps, n_features? Needed input_shape in first layer, which is Bid not LSTM
    model.add(SeqSelfAttention(attention_activation='sigmoid'))
    model.add(Dropout(0.3))
    
    model.add(GRU(512,return_sequences=True))
    model.add(Dropout(0.3))
    
    model.add(Flatten()) #Supposedly needed to fix stuff before dense layer
    model.add(Dense(n_vocab))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='rmsprop')

    # Load the weights to each node
    model.load_weights('1BiLSTMAtt1GruLayer-030-0.2558.hdf5')
    
    return model

def bilstm_attention_bigru(network_input, n_vocab):
    """ create the structure of the neural network """
    model = Sequential()

    model.add(Bidirectional(LSTM(512,return_sequences=True),input_shape=(network_input.shape[1], network_input.shape[2]))) #n_time_steps, n_features? Needed input_shape in first layer, which is Bid not LSTM
    model.add(SeqSelfAttention(attention_activation='sigmoid'))
    model.add(Dropout(0.3))
    
    model.add(Bidirectional(GRU(512,return_sequences=True)))
    model.add(Dropout(0.3))
    
    model.add(Flatten()) #Supposedly needed to fix stuff before dense layer
    model.add(Dense(n_vocab))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam')

    # Load the weights to each node
    model.load_weights('1BiLSTMAttBigruLayer-025-0.1574.hdf5')
    
    return model

def bilstm_attention_lstm(network_input, n_vocab):
    """ create the structure of the neural network """
    model = Sequential()

    model.add(Bidirectional(LSTM(512,return_sequences=True),input_shape=(network_input.shape[1], network_input.shape[2]))) #n_time_steps, n_features? Needed input_shape in first layer, which is Bid not LSTM
    model.add(SeqSelfAttention(attention_activation='sigmoid'))
    model.add(Dropout(0.3))
    
    model.add(LSTM(512,return_sequences=True))
    model.add(Dropout(0.3))
    
    model.add(Flatten()) #Supposedly needed to fix stuff before dense layer
    model.add(Dense(n_vocab))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam')

    # Load the weights to each node
    model.load_weights('1BiLSTMAtt1LSTMLayer-adam-030-0.0972.hdf5')
    
    return model

def lstm_network(network_input, n_vocab):
    """ create the structure of the neural network """
    model = Sequential()    
    model.add(LSTM(
        512,
        input_shape=(network_input.shape[1], network_input.shape[2]), #n_time_steps, n_features?
        return_sequences=True
    ))
    #model.add(SeqSelfAttention(attention_activation='sigmoid'))
    model.add(Dropout(0.3))
    model.add(Flatten()) #Supposedly needed to fix stuff before dense layers
    
    model.add(Dense(n_vocab))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='rmsprop')

    # Load the weights to each node
    model.load_weights('static/weights/lstm-20-0.1037-bigger.hdf5')
    
    return model

def lstm_attention(network_input, n_vocab):
    """ create the structure of the neural network """
    model = Sequential()    
    model.add(LSTM(
        512,
        input_shape=(network_input.shape[1], network_input.shape[2]), #n_time_steps, n_features?
        return_sequences=True
    ))
    model.add(SeqSelfAttention(attention_activation='sigmoid'))
    model.add(Dropout(0.3))
    model.add(Flatten()) #Supposedly needed to fix stuff before dense layers
    
    model.add(Dense(n_vocab))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam')

    # Load the weights to each node
    model.load_weights('static/weights/lstm-att-40-0.4609-bigger.hdf5')
    
    return model

def lstm_attention_lstm(network_input, n_vocab):
    """ create the structure of the neural network """
    model = Sequential()

    model.add(LSTM(512,return_sequences=True,input_shape=(network_input.shape[1], network_input.shape[2]))) #n_time_steps, n_features? Needed input_shape in first layer, which is Bid not LSTM
    model.add(SeqSelfAttention(attention_activation='sigmoid'))
    model.add(Dropout(0.3))
    
    model.add(LSTM(512,return_sequences=True))
    model.add(Dropout(0.3))
    
    model.add(Flatten()) #Supposedly needed to fix stuff before dense layer
    model.add(Dense(n_vocab))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam')

    # Load the weights to each node
    model.load_weights('static/weights/LSTMAtt-lstm-adam-030-0.1333.hdf5')
    
    return model

def lstm_lstm_lstm_network(network_input, n_vocab):
    """ create the structure of the neural network """
    model = Sequential()
    model.add(LSTM(
        512,
        input_shape=(network_input.shape[1], network_input.shape[2]),
        recurrent_dropout=0.3,
        return_sequences=True
    ))
    model.add(LSTM(512, return_sequences=True, recurrent_dropout=0.3,))
    model.add(LSTM(512))
    model.add(BatchNormalization())
    model.add(Dropout(0.3))
    model.add(Dense(256))
    model.add(Activation('relu'))
    model.add(BatchNormalization())
    model.add(Dropout(0.3))
    model.add(Dense(n_vocab))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='rmsprop')

    # Load the weights to each node
    model.load_weights('static/weights/lstm_lstm_lstm-40-5.5405-bigger.hdf5')
    
    return model

def lstm_bilstm_bilstm_network(network_input, n_vocab):
    """ create the structure of the neural network """
    model = Sequential()
    model.add(LSTM(512,input_shape=(network_input.shape[1], network_input.shape[2]),return_sequences=True))
    model.add(Dropout(0.3))
    model.add(Bidirectional(LSTM(512, return_sequences=True)))
    model.add(Dropout(0.3))
    model.add(Bidirectional(LSTM(512)))
    model.add(Dense(256))
    model.add(Dropout(0.3))
    model.add(Dense(n_vocab))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam')

    # Load the weights to each node
    model.load_weights('static/weights/lstm_bilstm_bilstm-20-2.3379-bigger.hdf5')
    
    return model

def gru_network(network_input, n_vocab):
    """ create the structure of the neural network """
    model = Sequential()
    model.add(GRU(512,return_sequences=True, input_shape = (network_input.shape[1], network_input.shape[2])))
    model.add(Dropout(0.3))
    model.add(Flatten()) #Supposedly needed to fix stuff before dense layers
    
    model.add(Dense(n_vocab))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adam')

    # Load the weights to each node
    model.load_weights('static/weights/gru-30-0.0998-bigger.hdf5')
    
    return model

def create_midi(prediction_output):
    """ convert the output from the prediction to notes and create a midi file
        from the notes """
    offset = 0
    output_notes = []

    # create note and chord objects based on the values generated by the model
    for pattern in prediction_output:
        pattern = pattern.split()
        temp = pattern[0]
        duration = pattern[1]
        pattern = temp
        # pattern is a chord
        if ('.' in pattern) or pattern.isdigit():
            notes_in_chord = pattern.split('.')
            notes = []
            for current_note in notes_in_chord:
                new_note = note.Note(int(current_note))
                new_note.storedInstrument = instrument.Piano()
                notes.append(new_note)
            new_chord = chord.Chord(notes)
            new_chord.offset = offset
            output_notes.append(new_chord)
        # pattern is a rest
        elif('rest' in pattern):
            new_rest = note.Rest(pattern)
            new_rest.offset = offset
            new_rest.storedInstrument = instrument.Piano() #???
            output_notes.append(new_rest)
        # pattern is a note
        else:
            new_note = note.Note(pattern)
            new_note.offset = offset
            new_note.storedInstrument = instrument.Piano()
            output_notes.append(new_note)

        # increase offset each iteration so that notes do not stack
        offset += convert_to_float(duration)

    midi_stream = stream.Stream(output_notes)

    midi_stream.write('midi', fp='static/generated_song.mid')

def convert_to_float(frac_str):
    try:
        return float(frac_str)
    except ValueError:
        num, denom = frac_str.split('/')
        try:
            leading, num = num.split(' ')
            whole = float(leading)
        except ValueError:
            whole = 0
        frac = float(num) / float(denom)
        return whole - frac if whole < 0 else whole + frac

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/results")
def results():
    return render_template("results.html")

@app.route("/lstm")
def lstm():
    return render_template("lstm.html")

@app.route("/gru")
def gru():
    return render_template("gru.html")

@app.route("/gan")
def gan():
    return render_template("gan.html")

@app.route("/bilstm_att")
def bilstm_att():
    return render_template("bilstm_att.html")

@app.route("/lstm_att")
def lstm_att():
    return render_template("lstm_att.html")

@app.route("/bilstm_att_bigru")
def bilstm_att_bigru():
    return render_template("bilstm_att_bigru.html")

@app.route("/bilstm_att_gru")
def bilstm_att_gru():
    return render_template("bilstm_att_gru.html")

@app.route("/bilstm_att_lstm")
def bilstm_att_lstm():
    return render_template("bilstm_att_lstm.html")

@app.route("/lstm_att_lstm")
def lstm_att_lstm():
    return render_template("lstm_att_lstm.html")

@app.route("/lstm_bilstm_bilstm")
def lstm_bilstm_bilstm():
    return render_template("lstm_bilstm_bilstm.html")

@app.route("/lstm_lstm_lstm")
def lstm_lstm_lstm():
    return render_template("lstm_lstm_lstm.html")

@app.route("/mozartandBeethoven")
def mozartbeethoven():
    return render_template("mozartbeethoven.html")

@app.route("/showHighScores",methods=["GET"])
def highscore():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("Select * from transactions ORDER BY score DESC;")
            user_scores = cursor.fetchall()
            return render_template("highscores.html", user_scores = user_scores)

@app.route("/survey")
def game():
    return render_template("game.html")

@app.route("/generate", methods=["GET","POST"])
def generation():
    #generate()
    if request.method == "POST":
        architecture_mode = request.form.get('architecture')
        dataset = request.form.get('dataset')
        note_number = request.form.get('notes')
        if dataset == 'mozart':
            generate_mozart(dataset, architecture_mode, int(note_number))
            a = True
            return render_template("generate.html", a = a)
    else:
        a = False
        return render_template("generate.html")

@app.route("/music")
def download():
    #generate()
    return render_template("music.html")  

@app.route("/final", methods=["GET","POST"])
def end():
    if request.method == "POST":
        name = request.form['name']
        score = request.form['score']
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO transactions (name, score) VALUES (%s,%s)",
                (name, int(score)),)
        with connection.cursor() as cursor:
            cursor.execute("Select * from transactions ORDER BY score DESC;")
            user_scores = cursor.fetchall()
            return render_template("highscores.html", user_scores = user_scores)
    else:
        return render_template("end.html")

if __name__ == "__main__":
    app.run(debug=True)
