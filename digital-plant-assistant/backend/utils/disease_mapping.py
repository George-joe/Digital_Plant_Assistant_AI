# backend/utils/disease_mapping.py

PLANTVILLAGE_MAPPING = {
    # Apple
    "Apple___Apple_scab": {
        "plant": "Apple",
        "disease": "Apple Scab",
        "severity": "medium",
        "basic_treatment": "Remove and destroy fallen leaves. Apply a copper-based fungicide. Ensure good air circulation by pruning."
    },
    "Apple___Black_rot": {
        "plant": "Apple",
        "disease": "Black Rot",
        "severity": "high",
        "basic_treatment": "Prune out dead or diseased wood. Remove mummified fruit. Apply a fungicide containing Captan or Myclobutanil."
    },
    "Apple___Cedar_apple_rust": {
        "plant": "Apple",
        "disease": "Cedar Apple Rust",
        "severity": "medium",
        "basic_treatment": "Remove nearby eastern red cedar hosts if possible. Apply preventative fungicides explicitly labeled for rust."
    },
    "Apple___healthy": {
        "plant": "Apple",
        "disease": "Healthy",
        "severity": "none",
        "basic_treatment": "Your Apple tree looks healthy! Maintain regular watering, adequate sunlight, and monitor for pests."
    },

    # Blueberry
    "Blueberry___healthy": {
        "plant": "Blueberry",
        "disease": "Healthy",
        "severity": "none",
        "basic_treatment": "Your Blueberry bush looks healthy! Keep soil acidic and ensure adequate moisture."
    },

    # Cherry
    "Cherry_(including_sour)___Powdery_mildew": {
        "plant": "Cherry",
        "disease": "Powdery Mildew",
        "severity": "medium",
        "basic_treatment": "Prune to improve airflow. Apply neem oil or a sulfur-based organic fungicide. Avoid overhead watering."
    },
    "Cherry_(including_sour)___healthy": {
        "plant": "Cherry",
        "disease": "Healthy",
        "severity": "none",
        "basic_treatment": "Your Cherry tree looks healthy! Continue providing deep watering during dry spells."
    },

    # Corn
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": {
        "plant": "Corn",
        "disease": "Gray Leaf Spot",
        "severity": "medium",
        "basic_treatment": "Ensure crop rotation in the future. Apply foliar fungicide if the disease reaches the ear leaf. Avoid overhead irrigation."
    },
    "Corn_(maize)___Common_rust_": {
        "plant": "Corn",
        "disease": "Common Rust",
        "severity": "medium",
        "basic_treatment": "Apply a fungicide early in the infection cycle. Plant rust-resistant varieties next season."
    },
    "Corn_(maize)___Northern_Leaf_Blight": {
        "plant": "Corn",
        "disease": "Northern Leaf Blight",
        "severity": "high",
        "basic_treatment": "Apply fungicides if lesions appear before silking. Practice tillage to reduce surface residue."
    },
    "Corn_(maize)___healthy": {
        "plant": "Corn",
        "disease": "Healthy",
        "severity": "none",
        "basic_treatment": "Your Corn looks healthy! Ensure it gets plenty of water and nitrogen as it grows."
    },

    # Grape
    "Grape___Black_rot": {
        "plant": "Grape",
        "disease": "Black Rot",
        "severity": "high",
        "basic_treatment": "Remove infected shoots, leaves, and mummified berries. Apply preventative fungicides starting early in the season."
    },
    "Grape___Esca_(Black_Measles)": {
        "plant": "Grape",
        "disease": "Esca (Black Measles)",
        "severity": "high",
        "basic_treatment": "There is no cure for Esca. Remove infected wood completely. Protect pruning wounds with paste."
    },
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": {
        "plant": "Grape",
        "disease": "Leaf Blight",
        "severity": "medium",
        "basic_treatment": "Ensure proper vineyard aeration. Apply Bordeaux mixture or other copper-based fungicides."
    },
    "Grape___healthy": {
        "plant": "Grape",
        "disease": "Healthy",
        "severity": "none",
        "basic_treatment": "Your Grapevine looks healthy! Prune regularly to maintain good airflow."
    },

    # Orange
    "Orange___Haunglongbing_(Citrus_greening)": {
        "plant": "Orange",
        "disease": "Citrus Greening",
        "severity": "high",
        "basic_treatment": "This disease is incurable. You must remove and destroy the infected tree to prevent spreading to others via psyllid bugs."
    },

    # Peach
    "Peach___Bacterial_spot": {
        "plant": "Peach",
        "disease": "Bacterial Spot",
        "severity": "medium",
        "basic_treatment": "Apply copper-based bactericides. Maintain tree vigor with proper fertilization and pruning."
    },
    "Peach___healthy": {
        "plant": "Peach",
        "disease": "Healthy",
        "severity": "none",
        "basic_treatment": "Your Peach tree looks healthy! Keep up the good care routines."
    },

    # Pepper, bell
    "Pepper,_bell___Bacterial_spot": {
        "plant": "Bell Pepper",
        "disease": "Bacterial Spot",
        "severity": "high",
        "basic_treatment": "Remove severely infected plants. Avoid overhead watering. Apply copper spray to slow the spread."
    },
    "Pepper,_bell___healthy": {
        "plant": "Bell Pepper",
        "disease": "Healthy",
        "severity": "none",
        "basic_treatment": "Your Bell Pepper plant looks healthy! Provide consistent moisture and watch for aphids."
    },

    # Potato
    "Potato___Early_blight": {
        "plant": "Potato",
        "disease": "Early Blight",
        "severity": "medium",
        "basic_treatment": "Remove infected leaves. Apply a fungicide containing chlorothalonil or copper. Avoid wetting the leaves when watering."
    },
    "Potato___Late_blight": {
        "plant": "Potato",
        "disease": "Late Blight",
        "severity": "high",
        "basic_treatment": "Highly contagious! Destroy infected plants immediately. Apply protective fungicides before periods of wet weather."
    },
    "Potato___healthy": {
        "plant": "Potato",
        "disease": "Healthy",
        "severity": "none",
        "basic_treatment": "Your Potato plant looks healthy! Ensure consistent soil moisture and consider hilling the soil."
    },

    # Raspberry
    "Raspberry___healthy": {
        "plant": "Raspberry",
        "disease": "Healthy",
        "severity": "none",
        "basic_treatment": "Your Raspberry bush looks healthy! Keep the soil moist and mulch well."
    },

    # Soybean
    "Soybean___healthy": {
        "plant": "Soybean",
        "disease": "Healthy",
        "severity": "none",
        "basic_treatment": "Your Soybean plant looks healthy! Ensure adequate watering during pod fill."
    },

    # Squash
    "Squash___Powdery_mildew": {
        "plant": "Squash",
        "disease": "Powdery Mildew",
        "severity": "medium",
        "basic_treatment": "Apply neem oil, sulfur spray, or a baking soda solution. Space plants out for better airflow."
    },

    # Strawberry
    "Strawberry___Leaf_scorch": {
        "plant": "Strawberry",
        "disease": "Leaf Scorch",
        "severity": "medium",
        "basic_treatment": "Remove infected leaves. Keep the foliage dry when watering. Clean up dead debris over winter."
    },
    "Strawberry___healthy": {
        "plant": "Strawberry",
        "disease": "Healthy",
        "severity": "none",
        "basic_treatment": "Your Strawberry plant looks healthy! Ensure they get plenty of sun and regular water."
    },

    # Tomato
    "Tomato___Bacterial_spot": {
        "plant": "Tomato",
        "disease": "Bacterial Spot",
        "severity": "high",
        "basic_treatment": "Remove infected leaves. Avoid overhead watering. Apply copper fungicides weekly."
    },
    "Tomato___Early_blight": {
        "plant": "Tomato",
        "disease": "Early Blight",
        "severity": "medium",
        "basic_treatment": "Remove the lower infected leaves. Apply organic copper fungicide. Water at the base of the plant."
    },
    "Tomato___Late_blight": {
        "plant": "Tomato",
        "disease": "Late Blight",
        "severity": "high",
        "basic_treatment": "Extremely destructive. Remove and destroy infected plants immediately. Apply fungicide to protect surrounding plants."
    },
    "Tomato___Leaf_Mold": {
        "plant": "Tomato",
        "disease": "Leaf Mold",
        "severity": "medium",
        "basic_treatment": "Increase ventilation to lower humidity. Remove infected lower leaves. Consider pruning to open the canopy."
    },
    "Tomato___Septoria_leaf_spot": {
        "plant": "Tomato",
        "disease": "Septoria Leaf Spot",
        "severity": "medium",
        "basic_treatment": "Remove infected bottom leaves. Mulch under the plant to prevent soil splashing. Apply fungicide."
    },
    "Tomato___Spider_mites Two-spotted_spider_mite": {
        "plant": "Tomato",
        "disease": "Spider Mites",
        "severity": "medium",
        "basic_treatment": "Spray plants with a strong stream of water to dislodge mites. Apply insecticidal soap or neem oil."
    },
    "Tomato___Target_Spot": {
        "plant": "Tomato",
        "disease": "Target Spot",
        "severity": "medium",
        "basic_treatment": "Improve airflow and reduce humidity. Remove severely infected leaves. Use a chlorothalonil-based spray if necessary."
    },
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": {
        "plant": "Tomato",
        "disease": "Yellow Leaf Curl Virus",
        "severity": "high",
        "basic_treatment": "Incurable virus spread by whiteflies. Remove and destroy the infected plant. Control whiteflies with insecticidal soap."
    },
    "Tomato___Tomato_mosaic_virus": {
        "plant": "Tomato",
        "disease": "Mosaic Virus",
        "severity": "high",
        "basic_treatment": "Highly contagious virus. Destroy infected plants immediately. Wash hands and tools thoroughly to prevent spreading."
    },
    "Tomato___healthy": {
        "plant": "Tomato",
        "disease": "Healthy",
        "severity": "none",
        "basic_treatment": "Your Tomato plant looks healthy! Provide deep watering and ensure it has sturdy support."
    }
}
