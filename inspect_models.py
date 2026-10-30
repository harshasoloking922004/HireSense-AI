import joblib

models = {
    "AI Resume Pipeline": "models/ai_resume_pipeline.pkl",
    "AI Resume Score Model": "models/ai_resume_score_model.pkl",
    "Job Role Classifier": "models/job_role_classifier.pkl",
    "Resume Preprocessor": "models/resume_preprocessor.pkl"
}


for name, path in models.items():

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    model = joblib.load(path)

    print("Type:", type(model).__name__)

    if hasattr(model, "steps"):
        print("\nPipeline steps:")

        for step_name, step_model in model.steps:
            print(
                f"  {step_name} -> "
                f"{type(step_model).__name__}"
            )

    if hasattr(model, "feature_names_in_"):
        print("\nFeature names:")
        print(model.feature_names_in_)

    if hasattr(model, "n_features_in_"):
        print("\nNumber of input features:")
        print(model.n_features_in_)

    if hasattr(model, "transformers_"):
        print("\nPreprocessor transformers:")

        for transformer in model.transformers_:
            print(transformer[0], "=>", type(transformer[1]).__name__)