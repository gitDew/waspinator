import glob
import logging
from waspinator.main import main
from ultralytics.models import YOLO

model = YOLO('./models/yolo26s-waspinator-chamber.pt', task='detect')

def test_main_on_trigger_images(caplog):
    caplog.set_level(logging.INFO)
    
    image_paths = glob.glob("test/images/TRIGGERED/*/*")
    total = len(image_paths)
    failures = []
    
    for image_path in image_paths:
        argv = [
            "start",
            "--dry-run",
            "--source",
            image_path
        ]
        caplog.clear()
        main(model=model, argv=argv)
        if not "FAKE TRAP TRIGGERED" in caplog.text:
            failures.append(image_path)
    
    ok = total - len(failures)
    pct = (ok / total * 100) if total else 0

    explanation = f"Out of {total} images with only velutinas on them, {ok} triggered the trap ({pct:.2f}%). Failures: {len(failures)}"

    print(explanation)
    if failures:
        with open("test_failures.csv", "w", newline="") as csvfile:
            for path in failures:
                csvfile.write(path + "\n")
            print(f"Wrote failures to test_failures.csv")

    assert pct >= 95, f"Model recall too low. {explanation}"

def test_main_on_no_op_images(caplog):
    caplog.set_level(logging.INFO)
    
    image_paths = glob.glob("test/images/NO_OP/*/*")
    total = len(image_paths)
    failures = []
    
    for image_path in image_paths:
        argv = [
            "start",
            "--dry-run",
            "--source",
            image_path
        ]
        caplog.clear()
        main(model=model, argv=argv)
        if "FAKE TRAP TRIGGERED" in caplog.text:
            failures.append(image_path)
    
    ok = total - len(failures)
    pct = (ok / total * 100) if total else 0
    false_positive_pct = 100 - pct

    explanation = f"Out of {total} images with NO velutinas on them, {len(failures)} triggered the trap incorrectly. (False positives: {false_positive_pct:.2f}%)."


    print(explanation)
    if failures:
        with open("false_positives.csv", "w", newline="") as csvfile:
            for path in failures:
                csvfile.write(path + "\n")
            print(f"Wrote failures to false_positives.csv")
    assert false_positive_pct < 5, f"Model false positives too high. {explanation}"
