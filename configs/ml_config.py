import os

ml_config = {
  "enable_ml_trade": False,
  "model_file": "ml/ml_models/mlp_model.txt",
  "scale_file": "ml/ml_models/mlp_scale.txt",
  "min_profitable_probablity": 0.999,
  "check_profitable_prediction": False,
  "check_loss_prediction": True,
  "max_loss_probablity": 0.85
}