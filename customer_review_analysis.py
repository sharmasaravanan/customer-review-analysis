# -*- coding: utf-8 -*-
# installing reqired libraries
"""### Data Acquisition and Preprocessing
#### Dataset Description and Acquisition
"""

import pandas as pd

# Load dataset (adjust path as necessary)
df = pd.read_csv('yelp.csv')
df.head()

"""#### Data Preprocessing"""

# Cleaning Text Data
import re
import nltk
from nltk.corpus import stopwords

nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

def clean_text(text):
    text = re.sub(r'<.*?>', '', text)  # Remove HTML tags
    text = re.sub(r'[^a-zA-Z\s]', '', text)  # Remove special characters
    text = text.lower()  # Convert to lowercase
    text = text.split()  # Tokenization
    text = [word for word in text if word not in stop_words]  # Remove stopwords
    text = ' '.join(text)  # Join tokens back to string
    return text

# Apply cleaning function to the reviews
df['cleaned_text'] = df['text'].apply(clean_text)
df['cleaned_text'].head()

# Handling Missing Values
missing_values = df.isnull().sum()
print("Missing values in each column:\n", missing_values)

# Drop missing values
df.dropna(inplace=True)
print("Data shape after dropping missing values:", df.shape)

df.describe()

"""#### 3. Exploratory Data Analysis (EDA)

"""

# Distribution of Ratings
import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(10, 6))
sns.countplot(x='stars', data=df)
plt.title('Distribution of Ratings')
plt.xlabel('Rating')
plt.ylabel('Count')
plt.show()

# Review Length Analysis
df['review_length'] = df['cleaned_text'].apply(len)

plt.figure(figsize=(10, 6))
sns.histplot(df['review_length'], bins=50, kde=True)
plt.title('Review Length Analysis')
plt.xlabel('Review Length')
plt.ylabel('Frequency')
plt.show()

# Common Words and Phrases
from collections import Counter

all_words = ' '.join(df['cleaned_text']).split()
word_counts = Counter(all_words)
common_words = word_counts.most_common(20)

common_words_df = pd.DataFrame(common_words, columns=['Word', 'Frequency'])

plt.figure(figsize=(10, 6))
sns.barplot(x='Frequency', y='Word', data=common_words_df)
plt.title('Common Words in Reviews')
plt.xlabel('Frequency')
plt.ylabel('Word')
plt.show()

# Sentiment Distribution
# Assuming sentiment is defined as positive (rating >= 4) and negative (rating < 4)
df['sentiment'] = df['stars'].apply(lambda x: 1 if x >= 3 else 0)

plt.figure(figsize=(10, 6))
sns.countplot(x='sentiment', data=df)
plt.title('Sentiment Distribution')
plt.xlabel('Sentiment (1: Positive, 0: Negative)')
plt.ylabel('Count')
plt.show()

# Visualization of Sentiment
from wordcloud import WordCloud

positive_reviews = ' '.join(df[df['sentiment'] == 1]['cleaned_text'])
negative_reviews = ' '.join(df[df['sentiment'] == 0]['cleaned_text'])

wordcloud_pos = WordCloud(width=800, height=400, background_color='white').generate(positive_reviews)
wordcloud_neg = WordCloud(width=800, height=400, background_color='white').generate(negative_reviews)

plt.figure(figsize=(16, 8))
plt.subplot(1, 2, 1)
plt.imshow(wordcloud_pos, interpolation='bilinear')
plt.title('Word Cloud for Positive Reviews')
plt.axis('off')

plt.subplot(1, 2, 2)
plt.imshow(wordcloud_neg, interpolation='bilinear')
plt.title('Word Cloud for Negative Reviews')
plt.axis('off')
plt.show()

"""#### Data Splitting (Training and Testing Sets)"""

# dealing with the class imbalance
df['stars'] = df['stars'].apply(lambda x: 0 if x <= 3 else 1)  # Combine 1, 2, 3 into 0 and 4, 5 into 1
group_0 = df[df['stars'] == 0].sample(3000, random_state=42)
group_1 = df[df['stars'] == 1].sample(3000, random_state=42)
balanced_df = pd.concat([group_0, group_1]).reset_index(drop=True)

balanced_df.head()

from sklearn.model_selection import train_test_split

X = balanced_df['cleaned_text']
y = balanced_df['stars']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

X.shape, X_train.shape, X_test.shape

"""#### RNN Model"""

# Training an RNN Model and Model Architecture
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import *
from tensorflow.keras.optimizers import Adam

# Tokenizing the text
tokenizer = Tokenizer(num_words=5000, lower=True, oov_token='<OOV>')
tokenizer.fit_on_texts(X_train)
word_index = tokenizer.word_index

# Convert text to sequences
X_train_seq = tokenizer.texts_to_sequences(X_train)
X_test_seq = tokenizer.texts_to_sequences(X_test)

# Padding sequences
max_length = 200
X_train_pad = pad_sequences(X_train_seq, maxlen=max_length)
X_test_pad = pad_sequences(X_test_seq, maxlen=max_length)

# Define the RNN model
rnn_model = Sequential()
rnn_model.add(Embedding(input_dim=5000, output_dim=128, input_length=max_length))
rnn_model.add(SpatialDropout1D(0.2))

rnn_model.add(LSTM(100, dropout=0.2, recurrent_dropout=0.2, return_sequences=True))
rnn_model.add(BatchNormalization())

rnn_model.add(LSTM(100, dropout=0.2, recurrent_dropout=0.2))
rnn_model.add(Dense(64, activation='relu'))
rnn_model.add(Dropout(0.2))

rnn_model.add(Dense(2, activation='softmax'))

optimizer = Adam(learning_rate=1e-4)
rnn_model.compile(loss='sparse_categorical_crossentropy', optimizer=optimizer, metrics=['accuracy'])

rnn_model.summary()

# Train the RNN model
history_rnn = rnn_model.fit(X_train_pad, y_train, epochs=10, batch_size=64, validation_data=(X_test_pad, y_test))

""" ##### Evaluation Metrics"""

# Plot Confusion Matrix
def plot_confusion_matrix(y_true, y_pred, title):
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Negative', 'Positive'], yticklabels=['Negative', 'Positive'])
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title(title)
    plt.show()

# Precision, Recall, F1 Score, and Confusion Matrix Analysis
from sklearn.metrics import classification_report, confusion_matrix

# Predicting using RNN model
rnn_predictions = rnn_model.predict(X_test_pad)
rnn_predictions = rnn_predictions.argmax(axis=1)

# Evaluation for RNN model
print("RNN Model Evaluation:")
print(classification_report(y_test, rnn_predictions))
plot_confusion_matrix(y_test, rnn_predictions, 'Confusion Matrix for RNN Model')

"""##### Real time data testing"""

def predict_sentiment_rnn(review):
    cleaned_review = clean_text(review)
    sequence = tokenizer.texts_to_sequences([cleaned_review])
    padded_sequence = pad_sequences(sequence, maxlen=max_length)
    prediction = rnn_model.predict(padded_sequence)
    index = prediction.argmax(axis=1)[0]
    sentiment = "Positive" if index > 0 else "Negative"
    print("Score:",max(prediction[0]))
    return sentiment

# Test the real-time functions
test_review = "The food was amazing and the service was excellent!"
print("RNN Model Prediction:", predict_sentiment_rnn(test_review))

test_review = "The food was awful and the service was worst ever i have seen!"
print("RNN Model Prediction:", predict_sentiment_rnn(test_review))

"""#### BERT Model"""

# Training a BERT Model and Model Architecture
from transformers import create_optimizer
from transformers import BertTokenizer, TFBertForSequenceClassification, Trainer, TrainingArguments
import tensorflow as tf

# Load BERT tokenizer and model
bert_tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
bert_model = TFBertForSequenceClassification.from_pretrained('bert-base-uncased',num_labels=2)

# Tokenize the dataset
inputs = bert_tokenizer(X_train.tolist(), return_tensors='tf', padding=True, truncation=True, max_length=512)
dataset = tf.data.Dataset.from_tensor_slices((inputs['input_ids'], inputs['attention_mask'],  y_train))

def encode_example(input_ids, attention_mask, label):
    return {"input_ids": input_ids, "attention_mask": attention_mask}, label

dataset = dataset.map(encode_example).batch(2)


test_inputs = bert_tokenizer(X_test.tolist(), return_tensors='tf', padding=True, truncation=True, max_length=512)
test_dataset = tf.data.Dataset.from_tensor_slices((test_inputs['input_ids'], test_inputs['attention_mask'],  y_test))

validationDataset = test_dataset.map(encode_example).batch(2)

# Define optimizer, loss, and metrics
num_train_steps = len(dataset) * 3  # Assuming 3 epochs
optimizer, schedule = create_optimizer(init_lr=2e-5, num_warmup_steps=0, num_train_steps=num_train_steps)
loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
metrics = [tf.keras.metrics.SparseCategoricalAccuracy('accuracy')]

# Compile the model with an appropriate optimizer, loss function, and metrics
bert_model.compile(optimizer=optimizer, loss=loss, metrics=metrics)

# summary of the model
bert_model.summary()

# training the model
history = bert_model.fit(dataset, validation_data= validationDataset, epochs=1)

"""##### Evaluation Metrics

"""

# Plot Confusion Matrix
def plot_confusion_matrix(y_true, y_pred, title):
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Negative', 'Positive'], yticklabels=['Negative', 'Positive'])
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title(title)
    plt.show()

# Predicting using BERT model

# Precision, Recall, F1 Score, and Confusion Matrix Analysis
from sklearn.metrics import classification_report, confusion_matrix

bert_predictions = bert_model.predict(validationDataset)

# Evaluation for BERT model
print("BERT Model Evaluation:")
print(classification_report(y_test, tf.argmax(bert_predictions.logits, axis=1)))
# print("Confusion Matrix:\n", confusion_matrix(y_test, tf.argmax(bert_predictions.logits, axis=1)))

plot_confusion_matrix(y_test, tf.argmax(bert_predictions.logits, axis=1), 'Confusion Matrix for BERT Model')

"""##### Real time data testing"""

# Real-Time Testing Function
def predict_sentiment_bert(review):
    # Tokenize the input text
    inputs = bert_tokenizer(review, return_tensors='tf', padding=True, truncation=True, max_length=512)

    # Make predictions
    outputs = bert_model(inputs)
    logits = outputs.logits

    # Convert logits to class predictions
    predictions = tf.argmax(logits, axis=1)
    score = predictions.numpy()[0]
    sentiment = "Positive" if score > 0.5 else "Negative"
    return sentiment

# Test the real-time functions
test_review = "The food was amazing and the service was excellent!"
print("BERT Model Prediction:", predict_sentiment_bert(test_review))

test_review = "The food was awful and the service was worst ever i have seen!"
print("BERT Model Prediction:", predict_sentiment_bert(test_review))

