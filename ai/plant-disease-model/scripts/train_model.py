import os
import tensorflow as tf
from tensorflow.keras import layers, models
import matplotlib.pyplot as plt
import json

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "..", "dataset", "PlantVillage", "PlantVillage")
MODEL_SAVE_PATH = os.path.join(BASE_DIR, "..", "model", "plant_disease_model.keras")
CLASSES_SAVE_PATH = os.path.join(BASE_DIR, "..", "model", "class_indices.json")
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 8

def train_model():
    print("Loading dataset...")
    
    # Load and split dataset
    train_ds = tf.keras.utils.image_dataset_from_directory(
        DATASET_DIR,
        validation_split=0.2,
        subset="training",
        seed=1337,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        label_mode='categorical'
    )
    
    val_ds = tf.keras.utils.image_dataset_from_directory(
        DATASET_DIR,
        validation_split=0.2,
        subset="validation",
        seed=1337,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        label_mode='categorical'
    )

    class_names = train_ds.class_names
    print(f"Detected classes: {class_names}")
    
    # Save class indices as a dictionary mapping index to name (CRITICAL FIX)
    class_indices_dict = {str(i): name for i, name in enumerate(class_names)}
    with open(CLASSES_SAVE_PATH, 'w') as f:
        json.dump(class_indices_dict, f, indent=4)
    print(f"Class indices saved to {CLASSES_SAVE_PATH}")

    # Configure dataset for performance
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

    # Data Augmentation & Preprocessing
    # FIX: Rescale by 1./255 to perfectly match the prediction code's normalization.
    rescale_layer = layers.Rescaling(1./255.0)
    
    data_augmentation = tf.keras.Sequential([
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.2),
        layers.RandomZoom(0.2),
    ], name="data_augmentation")

    # Build MobileNetV2 Model (Transfer Learning)
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights='imagenet'
    )
    base_model.trainable = False  # Freeze base layers initially

    inputs = tf.keras.Input(shape=(224, 224, 3))
    x = data_augmentation(inputs)
    x = rescale_layer(x)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(len(class_names), activation='softmax')(x)
    
    model = tf.keras.Model(inputs, outputs)

    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    model.summary()

    # Callbacks
    early_stopping = tf.keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=3,
        restore_best_weights=True,
        verbose=1
    )
    
    checkpoint = tf.keras.callbacks.ModelCheckpoint(
        filepath=MODEL_SAVE_PATH,
        monitor='val_loss',
        save_best_only=True,
        verbose=1
    )

    print("Starting training...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=[early_stopping, checkpoint]
    )

    print(f"Final manual save to {MODEL_SAVE_PATH}...")
    model.save(MODEL_SAVE_PATH)
    print("Training complete!")

if __name__ == "__main__":
    train_model()
