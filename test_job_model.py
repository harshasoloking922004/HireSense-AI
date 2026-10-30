import joblib

model = joblib.load("models/job_role_classifier.pkl")

print("=" * 60)
print("JOB ROLE CLASSIFIER")
print("=" * 60)

print("Model type:", type(model).__name__)

if hasattr(model, "steps"):
    print("\nPipeline steps:")
    for name, step in model.steps:
        print(f"{name} -> {type(step).__name__}")

if hasattr(model, "classes_"):
    print("\nClasses:")
    print(model.classes_)

if hasattr(model, "feature_names_in_"):
    print("\nFeature names:")
    print(model.feature_names_in_)

if hasattr(model, "n_features_in_"):
    print("\nNumber of features:")
    print(model.n_features_in_)

if hasattr(model, "get_feature_names_out"):
    try:
        features = model.get_feature_names_out()
        print("\nNumber of output features:", len(features))
    except Exception:
        pass

if hasattr(model, "named_steps"):
    print("\nDetailed pipeline:")
    for name, step in model.named_steps.items():
        print(f"\n{name}")
        print("Type:", type(step).__name__)

        if hasattr(step, "vocabulary_"):
            print("Vocabulary size:", len(step.vocabulary_))

        if hasattr(step, "classes_"):
            print("Classes:", step.classes_)