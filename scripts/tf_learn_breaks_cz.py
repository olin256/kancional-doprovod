import json

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

from break_utils import word_to_seq

with open("czwords.txt", "r", encoding="utf-8") as f:
    words = list(filter(None, (l.strip() for l in f if l[0] != "#")))

patterns = {}

for w in words:
    syllables = w.split("--")
    patterns["".join(syllables)] = [len(s) for s in syllables]

X = []
y = []

for word, pat in patterns.items():
    break_pos = [sum(pat[:k])-1 for k in range(1, len(pat))]
    break_vec = [(1 if i in break_pos else 0) for i in range(len(word))]

    y.append(break_vec)
    X.append(word_to_seq(word))


inp = layers.Input(shape=[None], dtype=tf.int16, ragged=True)
m = layers.Embedding(input_dim=len(chars)+1, output_dim=16)(inp) # , mask_zero=True
m = layers.Bidirectional(layers.LSTM(16, return_sequences=True))(m)
m = layers.TimeDistributed(layers.Dense(4, activation=keras.activations.relu))(m)
outp = layers.TimeDistributed(layers.Dense(1, activation=keras.activations.sigmoid))(m)

model = keras.Model(inputs=inp, outputs=tf.squeeze(outp, axis=-1))

model.compile(optimizer=tf.optimizers.Adam(), loss=keras.losses.BinaryCrossentropy(), metrics=[tf.metrics.BinaryAccuracy(name="accuracy")])

X = tf.ragged.constant(X)
y = tf.ragged.constant(y)

model.fit(X, y, epochs=80)

model.save("tf_cz_model.h5")

# test_slova = ["příhodný", "nestrannost", "představivý"]
# preds = model.predict(tf.ragged.constant([word_to_seq(w) for w in test_slova]))
# print(preds)