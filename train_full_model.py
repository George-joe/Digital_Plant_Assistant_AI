import os
import json
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau

def train_model():
    # Define paths
    base_dir = r"c:\Users\gkatt\Downloads\digital-plant-assistant-ai"
    dataset_dir = os.path.join(base_dir, "ai", "plant-disease-model", "dataset", "PlantVillage")
    model_dir = os.path.join(base_dir, "ai", "plant-disease-model", "model")
    
    os.makedirs(model_dir, exist_ok=True)
    
    model_save_path = os.path.join(model_dir, "plant_disease_model.keras")
    json_save_path = os.path.join(model_dir, "class_indices.json")
    
    # 1. Image Data Generators with Data Augmentation
    print("[INFO] Preparing data generators...")
    datagen = ImageDataGenerator(
        rescale=1./255,          # Normalize pixel values
        rotation_range=20,       # Rotate images
        width_shift_range=0.2,   # Shift horizontally
        height_shift_range=0.2,  # Shift vertically
        shear_range=0.2,         # Shear transformations
        zoom_range=0.2,          # Zoom in/out
        horizontal_flip=True,    # Flip horizontally
        fill_mode='nearest',
        validation_split=0.2     # 80/20 train/val split
    )
    
    # 2. Flow from Directory
    print("[INFO] Loading training data...")
    train_generator = datagen.flow_from_directory(
        dataset_dir,
        target_size=(224, 224),
        batch_size=32,
        class_mode='categorical',
        subset='training'
    )
    
    print("[INFO] Loading validation data...")
    val_generator = datagen.flow_from_directory(
        dataset_dir,
        target_size=(224, 224),
        batch_size=32,
        class_mode='categorical',
        subset='validation'
    )
    
    # 3. Save class_indices.json
    print("[INFO] Saving class indices mapping...")
    class_indices = train_generator.class_indices
    # Invert mapping to have idx -> class_name internally, but saving class -> idx is standard.
    # The backend supports {"0": "Apple___Apple_scab", ...} format:
    inverted_indices = {str(v): k for k, v in class_indices.items()}
    with open(json_save_path, 'w') as f:
        json.dump(inverted_indices, f, indent=4)
    print(f"[INFO] Class indices saved to {json_save_path} (Total Classes: {len(inverted_indices)})")
    
    # 4. Build Model (MobileNetV2 base)
    print("[INFO] Building MobileNetV2 model...")
    base_model = MobileNetV2(
        weights='imagenet',
        include_top=False,
        input_shape=(224, 224, 3)
    )
    
    # Freeze the base model for initial training
    base_model.trainable = False
    
    # Add custom classification head
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(128, activation='relu')(x)
    predictions = Dense(train_generator.num_classes, activation='softmax')(x)
    
    model = Model(inputs=base_model.input, outputs=predictions)
    
    # 5. Compile Model
    print("[INFO] Compiling model...")
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # 6. Callbacks
    # Save the best model automatically
    checkpoint = ModelCheckpoint(model_save_path, monitor='val_loss', save_best_only=True, verbose=1)
    # Stop early if learning stales
    early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True, verbose=1)
    # Reduce learning rate if plateau
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, verbose=1)
    
    # 7. Train Model
    epochs = 15
    print(f"[INFO] Starting training for {epochs} epochs...")
    history = model.fit(
        train_generator,
        epochs=epochs,
        validation_data=val_generator,
        callbacks=[checkpoint, early_stop, reduce_lr]
    )
    
    # 8. Unfreeze and Fine-Tune (Optional, but helps with accuracy)
    print("[INFO] Unfreezing base model for fine-tuning...")
    base_model.trainable = True
    
    # Recompile with a very low learning rate for fine-tuning
    model.compile(
        optimizer=Adam(learning_rate=1e-5),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    print("[INFO] Starting fine-tuning for 5 epochs...")
    history_fine = model.fit(
        train_generator,
        epochs=5,
        validation_data=val_generator,
        callbacks=[checkpoint, early_stop]
    )
    
    print(f"[INFO] Training Complete! Final model saved to: {model_save_path}")

if __name__ == "__main__":
    train_model()
