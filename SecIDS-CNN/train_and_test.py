#!/usr/bin/env python3
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
try:
    import tensorflow as tf
    from tensorflow import keras  # type: ignore
    USE_TF = True
except Exception as e:
    print(f"⚠️ TensorFlow import failed: {e}\n  Falling back to scikit-learn classifier.")
    USE_TF = False
from sklearn.ensemble import RandomForestClassifier
import warnings
import sys
from pathlib import Path

warnings.filterwarnings('ignore')

# Import progress utilities
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / 'Tools'))
    from progress_utils import (DataLoadingProgress, PreprocessingProgress, 
                                 TrainingProgress, PredictionProgress)
    PROGRESS_AVAILABLE = True
except ImportError:
    PROGRESS_AVAILABLE = False
    print("⚠️  Progress utilities not available")

print("="*80)
print("THREAT DETECTION MODEL - TRAINING AND TESTING")
print("="*80)

# Load DDoS training dataset
import os
# Use master dataset if available, fallback to archived ddos dataset
master_dataset_path = os.path.join(os.path.dirname(__file__), 'datasets', 'MD_1.csv')
archive_dataset_path = os.path.join(os.path.dirname(__file__), '..', 'Archives', 'ddos_training_dataset.csv')

if os.path.exists(master_dataset_path):
    data_path = master_dataset_path
    print("\n✓ Using master dataset")
elif os.path.exists(archive_dataset_path):
    data_path = archive_dataset_path
    print("\n⚠️  Using archived dataset (master not found)")
else:
    data_path = os.path.join(os.path.dirname(__file__), 'datasets', 'ddos_training_dataset.csv')
    print("\n⚠️  Using fallback dataset path")

print(f"\nLoading dataset from: {data_path}")
try:
    df = pd.read_csv(data_path)
    print(f"✓ Loaded successfully! ({df.shape[0]} rows, {df.shape[1]} columns)")
    numeric_cols = df.select_dtypes(include=[np.number]).shape[1]
    print(f"  Numeric columns: {numeric_cols}")
except FileNotFoundError as e:
    print(f"✗ Error: Dataset file not found - {e}")
    raise
except Exception as e:
    print(f"✗ Error loading dataset: {str(e)[:60]}")
    raise

try:
    print(f"\n[1/5] Data Overview")
    print(f"{'='*80}")
    print(f"  - Total records: {len(df):,}")
    print(f"  - Total columns: {len(df.columns)}")
    print(f"  - Columns: {df.columns.tolist()}")
    
    print(f"\n  First 5 rows:")
    print(df.head().to_string())
    
    # Check for missing values
    missing_count = df.isnull().sum().sum()
    print(f"\n  Missing values: {missing_count}")
    if missing_count > 0:
        print(f"  - Removing missing values...")
    
    # Data preprocessing
    print(f"\n[2/5] Data Preprocessing")
    print(f"{'='*80}")
    
    # Remove rows with missing values
    df = df.dropna()
    print(f"  ✓ Records after cleaning: {len(df):,}")
    
    # Identify target column
    target_col = None
    possible_targets = ['is_attack', 'Attack', 'attack', 'Label', 'Class', 'label', 
                       'class', 'Type', 'type', 'threat', 'Threat', 'Intrusion']
    
    for col in possible_targets:
        if col in df.columns:
            target_col = col
            break
    
    # If no target found, create one based on statistical anomalies
    if target_col is None:
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) > 0:
            # Calculate anomaly score based on statistical outliers
            z_scores = np.abs((numeric_df - numeric_df.mean()) / numeric_df.std())
            anomaly_score = z_scores.max(axis=1)
            df['anomaly'] = (anomaly_score > 2).astype(int)
            target_col = 'anomaly'
        else:
            raise ValueError("No suitable target column found and cannot create one")
    
    print(f"  ✓ Target column: {target_col}")
    
    # Check target distribution
    if df[target_col].dtype == 'object':
        print(f"  - Target classes: {df[target_col].unique().tolist()}")
    else:
        print(f"  - Target values: {sorted(df[target_col].unique().tolist())}")
    
    # Separate features and target
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Encode categorical variables
    categorical_cols = X.select_dtypes(include=['object']).columns.tolist()
    label_encoders = {}
    
    for col in categorical_cols:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        label_encoders[col] = le
    
    print(f"  ✓ Encoded {len(categorical_cols)} categorical columns")
    
    # Encode target if categorical
    if y.dtype == 'object':
        y_encoder = LabelEncoder()
        y = y_encoder.fit_transform(y.astype(str))
        class_names = list(y_encoder.classes_)
    else:
        class_names = sorted(list(set(y)))
    
    print(f"  - Classes to predict: {class_names}")
    
    # Select only numeric features
    X = X.select_dtypes(include=[np.number])
    print(f"  ✓ Total features: {X.shape[1]}")
    
    # Normalize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print(f"  ✓ Features normalized")
    
    # Split data
    print(f"\n[3/5] Train/Test Split")
    print(f"{'='*80}")
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"  - Training set: {X_train.shape[0]:,} samples")
    print(f"  - Test set: {X_test.shape[0]:,} samples")
    print(f"  - Feature dimension: {X_train.shape[1]}")
    
    # Build optimized model (TensorFlow if available, otherwise scikit-learn fallback)
    print(f"\n[4/5] Building Neural Network Model")
    print(f"{'='*80}")

    num_classes = len(set(y))
    input_dim = X_train.shape[1]

    if USE_TF:
        # Determine model architecture based on input dimension
        if input_dim <= 10:
            # Small input - use simple dense network
            model = keras.Sequential([
                keras.layers.Dense(64, activation='relu', input_dim=input_dim),
                keras.layers.BatchNormalization(),
                keras.layers.Dropout(0.3),
                keras.layers.Dense(32, activation='relu'),
                keras.layers.Dropout(0.2),
                keras.layers.Dense(16, activation='relu'),
                keras.layers.Dense(num_classes, activation='softmax' if num_classes > 1 else 'sigmoid')
            ])
        else:
            # Medium input - use CNN with proper padding
            X_train_reshaped = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
            X_test_reshaped = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)

            model = keras.Sequential([
                keras.layers.Conv1D(32, kernel_size=3, activation='relu', padding='same', input_shape=(input_dim, 1)),
                keras.layers.BatchNormalization(),
                keras.layers.MaxPooling1D(pool_size=2, padding='same'),

                keras.layers.Conv1D(64, kernel_size=3, activation='relu', padding='same'),
                keras.layers.BatchNormalization(),
                keras.layers.GlobalAveragePooling1D(),

                keras.layers.Dense(128, activation='relu'),
                keras.layers.Dropout(0.4),
                keras.layers.Dense(64, activation='relu'),
                keras.layers.Dropout(0.3),
                keras.layers.Dense(num_classes, activation='softmax' if num_classes > 1 else 'sigmoid')
            ])

        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy' if num_classes > 1 else 'binary_crossentropy',
            metrics=['accuracy']
        )

        print(f"  - Model type: {'CNN' if input_dim > 10 else 'Dense Neural Network'}")
        print(f"  - Output classes: {num_classes}")
        try:
            print(f"  - Total parameters: {model.count_params():,}")
        except Exception as e:
            pass  # Skip on error
        # Train model
        print(f"\n[5/5] Training Model")
        print(f"{'='*80}")

        # Create custom callback for progress bar
        if PROGRESS_AVAILABLE:
            from tqdm.keras import TqdmCallback
            
            if input_dim > 10:
                history = model.fit(
                    X_train_reshaped, y_train,
                    epochs=15,
                    batch_size=32,
                    validation_split=0.1,
                    verbose=0,
                    callbacks=[TqdmCallback(verbose=1)]
                )
            else:
                history = model.fit(
                    X_train, y_train,
                    epochs=15,
                    batch_size=32,
                    validation_split=0.1,
                    verbose=0,
                    callbacks=[TqdmCallback(verbose=1)]
                )
        else:
            if input_dim > 10:
                history = model.fit(
                    X_train_reshaped, y_train,
                    epochs=15,
                    batch_size=32,
                    validation_split=0.1,
                    verbose=1
                )
            else:
                history = model.fit(
                    X_train, y_train,
                    epochs=15,
                    batch_size=32,
                    validation_split=0.1,
                    verbose=1
                )

        print(f"\n  ✓ Training completed!")
        print(f"  - Training accuracy: {history.history['accuracy'][-1]:.4f}")
        print(f"  - Validation accuracy: {history.history['val_accuracy'][-1]:.4f}")
    else:
        # scikit-learn fallback (RandomForest)
        print("  - Using scikit-learn RandomForestClassifier fallback (no TensorFlow detected)")
        # create a small validation split from the training set
        X_train_sub, X_val_sub, y_train_sub, y_val_sub = train_test_split(
            X_train, y_train, test_size=0.1, random_state=42, stratify=y_train
        )
        model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        print(f"\n[5/5] Training Model (sklearn)")
        print(f"{'='*80}")
        model.fit(X_train_sub, y_train_sub)
        train_acc = model.score(X_train_sub, y_train_sub)
        val_acc = model.score(X_val_sub, y_val_sub)
        print(f"  ✓ Training completed!")
        print(f"  - Training accuracy: {train_acc:.4f}")
        print(f"  - Validation accuracy: {val_acc:.4f}")
    
    # Evaluate model
    print(f"\n{'='*80}")
    print("RESULTS SUMMARY")
    print(f"{'='*80}")
    
    # Evaluate model and produce reports
    from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support, accuracy_score

    if USE_TF:
        if input_dim > 10:
            test_loss, test_accuracy = model.evaluate(X_test_reshaped, y_test, verbose=0)
            y_pred = model.predict(X_test_reshaped, verbose=0)
        else:
            test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=0)
            y_pred = model.predict(X_test, verbose=0)

        y_pred_classes = np.argmax(y_pred, axis=1) if num_classes > 1 else (y_pred > 0.5).astype(int).flatten()
        print(f"\n✓ TEST ACCURACY: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")
        print(f"✓ TEST LOSS: {test_loss:.4f}")

    else:
        # sklearn evaluation
        y_pred = model.predict(X_test)
        test_accuracy = accuracy_score(y_test, y_pred)
        test_loss = 0.0
        y_pred_classes = y_pred
        print(f"\n✓ TEST ACCURACY: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")

    print(f"\n{'='*80}")
    print("DETAILED CLASSIFICATION REPORT")
    print(f"{'='*80}\n")

    class_names_list = [str(c) for c in class_names]
    try:
        print(classification_report(y_test, y_pred_classes, target_names=class_names_list))
    except Exception:
        print(classification_report(y_test, y_pred_classes))

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred_classes)
    print(f"Confusion Matrix:")
    print(cm)

    # Per-class metrics
    precision, recall, f1, support = precision_recall_fscore_support(y_test, y_pred_classes, average=None)

    print(f"\n{'='*80}")
    print("PER-CLASS PERFORMANCE METRICS")
    print(f"{'='*80}\n")
    print(f"{'Class':<20}{'Precision':<15}{'Recall':<15}{'F1-Score':<15}{'Support'}")
    print("-" * 80)
    for i, class_name in enumerate(class_names_list):
        print(f"{class_name:<20}{precision[i]:<15.4f}{recall[i]:<15.4f}{f1[i]:<15.4f}{int(support[i])}")  # type: ignore

    # Sample predictions
    print(f"\n{'='*80}")
    print("SAMPLE PREDICTIONS (First 15 test samples)")
    print(f"{'='*80}\n")
    print(f"{'Index':<8}{'Predicted':<20}{'Actual':<20}{'Confidence':<12}{'Status'}")
    print("-" * 75)

    for i in range(min(15, len(y_test))):
        pred_class = int(y_pred_classes[i])
        actual_class = y_test.iloc[i] if hasattr(y_test, 'iloc') else y_test[i]
        confidence = np.max(y_pred[i]) if (USE_TF and hasattr(y_pred[i], '__iter__')) else 1.0

        pred_name = class_names_list[pred_class] if pred_class < len(class_names_list) else str(pred_class)
        actual_name = class_names_list[actual_class] if actual_class < len(class_names_list) else str(actual_class)

        match = "✓ Correct" if pred_class == actual_class else "✗ Wrong"
        print(f"{i:<8}{pred_name:<20}{actual_name:<20}{confidence:<12.4f}{match}")

    # Summary
    print(f"\n{'='*80}")
    print("MODEL TRAINING COMPLETE!")
    print(f"{'='*80}")

    correct_predictions = np.sum(np.array(y_pred_classes) == np.array(y_test))
    total_predictions = len(y_test)
    accuracy_percent = (correct_predictions / total_predictions) * 100

    print(f"\nFINAL SUMMARY:")
    print(f"  ✓ Correct predictions: {correct_predictions:,} / {total_predictions:,}")
    print(f"  ✓ Overall accuracy: {accuracy_percent:.2f}%")
    print(f"  ✓ Number of features used: {input_dim}")
    print(f"  ✓ Number of classes: {num_classes}")
    print(f"  ✓ Test set size: {len(y_test):,} samples")
    try:
        params_info = model.count_params() if USE_TF else 'N/A (sklearn model)'
        print(f"  ✓ Model parameters: {params_info}")
    except Exception as e:
            pass  # Skip on error
    # Save model
    try:
        if USE_TF:
            model.save('./SecIDS-CNN.h5')
            print(f"\n✓ Model successfully saved: SecIDS-CNN.h5")
        else:
            import joblib
            joblib.dump(model, './SecIDS-CNN_rf.pkl')
            print(f"\n✓ Sklearn model successfully saved: SecIDS-CNN_rf.pkl")
    except Exception as e:
        print(f"\n⚠️ Model save failed: {e}")
    
except Exception as e:
    print(f"\n✗ Error occurred: {e}")
    import traceback
    traceback.print_exc()
