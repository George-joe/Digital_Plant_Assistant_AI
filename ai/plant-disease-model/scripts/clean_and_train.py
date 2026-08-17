"""
clean_and_train.py
==================
Step 1: Clean the dataset — rename all class folders to strict triple-underscore format.
Step 2: Remove corrupted / non-image files.
Step 3: Retrain MobileNetV2 with data augmentation.
Step 4: Save best model + correct class_indices.json.

Run from project root:
  python ai/plant-disease-model/scripts/clean_and_train.py
"""

import os
import re
import shutil
import json
import sys

# ─── Paths ─────────────────────────────────────────────────────────────────────
BASE   = os.path.dirname(os.path.abspath(__file__))
DATASET_ROOT = os.path.normpath(os.path.join(BASE, "..", "dataset", "PlantVillage"))
MODEL_DIR    = os.path.normpath(os.path.join(BASE, "..", "model"))
MODEL_PATH   = os.path.join(MODEL_DIR, "plant_disease_model.keras")
CLASSES_PATH = os.path.join(MODEL_DIR, "class_indices.json")
VALID_EXT    = {".jpg", ".jpeg", ".png", ".bmp"}

# ─── STEP 1: CANONICAL CLASS NAME MAP ──────────────────────────────────────────
# Maps any observed folder naming variant → canonical "Plant___Disease" name.
# Uses triple underscore (___) per user requirement.
PERMITTED_CLASSES = {
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___Healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___Healthy",
    "Pepper___Bacterial_spot",
    "Pepper___Healthy"
}

CANONICAL = {
    # Pepper variants
    "Pepper__bell___Bacterial_spot":  "Pepper___Bacterial_spot",
    "Pepper__bell___healthy":         "Pepper___Healthy",
    "Pepper,_bell___Bacterial_spot":  "Pepper___Bacterial_spot",
    "Pepper,_bell___healthy":         "Pepper___Healthy",
    "Pepper___Bacterial_spot":        "Pepper___Bacterial_spot",
    "Pepper___Healthy":               "Pepper___Healthy",
    "Pepper___healthy":               "Pepper___Healthy",

    # Potato
    "Potato___Early_blight":          "Potato___Early_blight",
    "Potato___Late_blight":           "Potato___Late_blight",
    "Potato___healthy":               "Potato___Healthy",
    "Potato___Healthy":               "Potato___Healthy",

    # Tomato mapping
    "Tomato_Early_blight":            "Tomato___Early_blight",
    "Tomato_Late_blight":             "Tomato___Late_blight",
    "Tomato_Leaf_Mold":               "Tomato___Leaf_Mold",
    "Tomato_Septoria_leaf_spot":      "Tomato___Septoria_leaf_spot",
    "Tomato__Target_Spot":            "Tomato___Target_Spot",
    "Tomato__Tomato_YellowLeaf__Curl_Virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Yellow_Leaf_Curl_Virus":       "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato__Tomato_mosaic_virus":    "Tomato___Tomato_mosaic_virus",
    "Tomato___Mosaic_Virus":          "Tomato___Tomato_mosaic_virus",
    "Tomato_healthy":                 "Tomato___Healthy",
    
    # Triple underscore correct
    "Tomato___Early_blight":          "Tomato___Early_blight",
    "Tomato___Late_blight":           "Tomato___Late_blight",
    "Tomato___Leaf_Mold":             "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot":    "Tomato___Septoria_leaf_spot",
    "Tomato___Target_Spot":          "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus":   "Tomato___Tomato_mosaic_virus",
    "Tomato___Healthy":               "Tomato___Healthy",
    "Tomato___healthy":               "Tomato___Healthy",
}


def is_valid_image(path):
    ext = os.path.splitext(path)[1].lower()
    if ext not in VALID_EXT:
        return False
    # Use PIL to verify without locking the file like CV2 sometimes does
    try:
        from PIL import Image
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


# ─── STEP 1+2: Clean Dataset ────────────────────────────────────────────────────
def clean_dataset(root):
    print(f"\n{'='*60}")
    print(f"STEP 1: Cleaning dataset at: {root}")
    print(f"{'='*60}")

    if not os.path.exists(root):
        print(f"[ERROR] Dataset root does not exist: {root}")
        sys.exit(1)

    existing = sorted(os.listdir(root))
    print(f"Found {len(existing)} folders: {existing}")

    # First pass: rename to canonical
    renamed = []
    for folder in existing:
        src = os.path.join(root, folder)
        if not os.path.isdir(src):
            continue
        canonical = CANONICAL.get(folder, folder)
        
        if canonical not in PERMITTED_CLASSES:
            print(f"  [DELETE] Forbidden non-whitelisted class: '{folder}'")
            try:
                shutil.rmtree(src)
            except PermissionError as e:
                print(f"  [WARN] PermissionError removing '{src}': {e}. Skipping deletion of folder.")
            continue

        if folder == canonical:
            print(f"  [OK]   '{folder}' already canonical.")
            renamed.append(canonical)
        else:
            dst = os.path.join(root, canonical)
            if os.path.exists(dst):
                # Merge: move all files from src into existing dst
                print(f"  [MERGE] '{folder}' → '{canonical}' (merge into existing)")
                for f in os.listdir(src):
                    fsrc = os.path.join(src, f)
                    fdst = os.path.join(dst, f)
                    if not os.path.exists(fdst):
                        shutil.move(fsrc, fdst)
                shutil.rmtree(src)
            else:
                print(f"  [RENAME] '{folder}' → '{canonical}'")
                os.rename(src, dst)
            renamed.append(canonical)

    # Second pass: remove corrupted / non-image files
    print(f"\nSTEP 2: Removing invalid files...")
    total_removed = 0
    for cls_folder in os.listdir(root):
        cls_path = os.path.join(root, cls_folder)
        if not os.path.isdir(cls_path):
            continue
        for fname in os.listdir(cls_path):
            fpath = os.path.join(cls_path, fname)
            if not is_valid_image(fpath):
                try:
                    os.remove(fpath)
                    print(f"  [REMOVE] Invalid file: {fpath}")
                    total_removed += 1
                except Exception as e:
                    print(f"  [WARN] Could not remove {fpath}: {e}")

    final_classes = sorted([d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))])
    print(f"\n[OK] Dataset cleaned. {total_removed} invalid files removed.")
    print(f"Final classes ({len(final_classes)}): {final_classes}")
    return final_classes


# ─── STEP 3+4: Retrain Model ────────────────────────────────────────────────────
def train_model(dataset_dir, model_path, classes_path):
    print(f"\n{'='*60}")
    print(f"STEP 3: Training MobileNetV2 on: {dataset_dir}")
    print(f"{'='*60}")

    import tensorflow as tf
    from tensorflow.keras import layers

    IMAGE_SIZE  = (224, 224)
    BATCH_SIZE  = 32
    EPOCHS      = 20

    # Load datasets
    train_ds = tf.keras.utils.image_dataset_from_directory(
        dataset_dir,
        validation_split=0.2,
        subset="training",
        seed=42,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="categorical"
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        dataset_dir,
        validation_split=0.2,
        subset="validation",
        seed=42,
        image_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="categorical"
    )

    class_names = train_ds.class_names
    num_classes = len(class_names)
    print(f"Classes detected ({num_classes}): {class_names}")

    # STEP 4: Save class_indices.json BEFORE training (in case of crash)
    class_indices = {str(i): name for i, name in enumerate(class_names)}
    os.makedirs(os.path.dirname(classes_path), exist_ok=True)
    with open(classes_path, "w") as f:
        json.dump(class_indices, f, indent=4)
    print(f"[OK] class_indices.json saved: {classes_path}")

    # Performance optimisation
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
    val_ds   = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

    # Data Augmentation — applied INSIDE model so preprocessing matches inference
    data_augmentation = tf.keras.Sequential([
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.15),
        layers.RandomZoom(0.15),
        layers.RandomContrast(0.1),
    ], name="data_augmentation")

    # Rescaling 0-255 → 0-1 to match inference preprocessing
    rescale = layers.Rescaling(1.0 / 255.0)

    # MobileNetV2 backbone
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights="imagenet"
    )
    base_model.trainable = False  # Freeze for phase 1

    # Build model
    inputs  = tf.keras.Input(shape=(224, 224, 3))
    x = data_augmentation(inputs)
    x = rescale(x)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=4,
            restore_best_weights=True, verbose=1
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=model_path,
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=2, verbose=1
        )
    ]

    # Phase 1: Train top layers only
    print(f"\n[Phase 1] Training top layers ({EPOCHS} epochs max)...")
    model.fit(
        train_ds, validation_data=val_ds,
        epochs=EPOCHS, callbacks=callbacks
    )

    # Phase 2: Fine-tune last 30 layers of MobileNetV2
    print("\n[Phase 2] Fine-tuning last 30 layers of MobileNetV2...")
    base_model.trainable = True
    for layer in base_model.layers[:-30]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-5),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )

    model.fit(
        train_ds, validation_data=val_ds,
        epochs=10,
        callbacks=callbacks
    )

    # Final save
    model.save(model_path)
    print(f"\n[OK] Model saved: {model_path}")
    print(f"[OK] class_indices.json: {classes_path}")
    print("\n=== TRAINING COMPLETE ===")
    print(f"Classes: {class_names}")


# ─── MAIN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    classes = clean_dataset(DATASET_ROOT)
    if not classes:
        print("[ERROR] No valid classes found after cleaning. Aborting.")
        sys.exit(1)
    train_model(DATASET_ROOT, MODEL_PATH, CLASSES_PATH)
