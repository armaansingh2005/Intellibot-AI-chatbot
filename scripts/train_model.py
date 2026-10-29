"""Train and evaluate the offline intent classifier."""

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import joblib
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from chatbot.intent_classifier import build_classifier, read_examples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/intents.json"))
    parser.add_argument("--output", type=Path, default=Path("instance/models/intent_classifier.joblib"))
    args = parser.parse_args()

    texts, labels = read_examples(args.data)
    counts = {label: labels.count(label) for label in set(labels)}
    if min(counts.values()) < 2:
        raise SystemExit("Each intent needs at least two examples for a stratified evaluation.")
    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels,
    )
    evaluation_model = build_classifier().fit(x_train, y_train)
    predictions = evaluation_model.predict(x_test)
    print(f"Evaluation examples: {len(y_test)} (held-out stratified split; random_state=42)")
    print(f"Accuracy: {accuracy_score(y_test, predictions):.4f}")
    print(classification_report(y_test, predictions, zero_division=0))

    final_model = build_classifier().fit(texts, labels)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_model, args.output)
    print(f"Trained on all {len(texts)} examples and saved to {args.output}")


if __name__ == "__main__":
    main()
