from flask import Flask, request, jsonify
from flask_cors import CORS
from normaliser import normalise_data
import pandas as pd
import formatter
from pca_logic import get_pca_suggestions

app = Flask(__name__)
CORS(app)

@app.route("/upload", methods=["GET", "POST"])
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        df = pd.read_csv(file)
        result = {"data": df.to_dict(orient="records")}
        format_result = formatter.format_data(result)
        return jsonify(format_result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/normalise", methods=["POST"])
def normalise_and_suggest():
    
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        df = pd.read_csv(file)
        
        # --- Run Normalisation (Critical Step) ---
        normalization_results = normalise_data(df)
        
        # --- Run PCA Suggestions (Optional Step) ---
        pca_suggestions = None  # Default to None
        try:
            # The file pointer is at the end after the first read, so we reset it
            file.seek(0)
            df_for_pca = pd.read_csv(file)
            pca_suggestions = get_pca_suggestions(df_for_pca)
            print("PCA suggestions generated successfully.")
        except Exception as pca_error:
            print("--- WARNING: PCA suggestion step failed. --- ")
            import traceback
            traceback.print_exc()
            print(f"PCA Error: {pca_error}")
            print("--- Proceeding without PCA suggestions. ---")

        # --- Combine Results ---
        combined_result = {
            "normalization_data": normalization_results,
            "pca_suggestions": pca_suggestions  # This will be None if PCA failed
        }
        
        print("Returning JSON with normalization data.")
        return jsonify(combined_result)
    
    except Exception as e:
        # This will now only catch critical errors (e.g., in file reading or normalization)
        print("--- CRITICAL: A non-recoverable error occurred. ---")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
