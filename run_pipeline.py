# run_pipeline.py

import sys
from src import data_preprocessing
from src.expiry_prediction import predict_expiry_class
from src.forecasting import main as forecast_main
from src.risk_scoring import main as risk_main
from src.recommendations.recommend import run_recommendation_pipeline

def run_pipeline(uploaded_file_path):
    print("🔧 Step 1: Data Preprocessing")
    data_preprocessing.main(uploaded_file_path)

    print("\n🧠 Step 2: Predicting Expiry Class (using saved model)")
    predict_expiry_class()  # Adds Expiry_Class to processed_data.csv

    print("\n📈 Step 3: Forecasting (using saved / skip if exists)")
    try:
        forecast_main()
    except Exception as e:
        print(f"⚠️ Forecast step skipped: {e}")

    print("\n⚖️ Step 4: Risk Scoring")
    risk_main()

    print("\n🎯 Step 5: Recommendation Engine")
    run_recommendation_pipeline()

    print("\n✅ Pipeline completed successfully. Output: data/external/recommendations.csv")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Please provide the uploaded CSV path.")
    else:
        run_pipeline(sys.argv[1])
