import cv2
from ultralytics import YOLO

model = YOLO('yolov8x.pt')

def detect_objects(image_path):
    image = cv2.imread(image_path)

    if image is None:
        print(f"Error: Could not load image at {image_path}")
        return

    results = model(image)

    detections = results[0].boxes
    print(f"Detected {len(detections)} objects in the image.")

    for box in detections:
        x1, y1, x2, y2 = box.xyxy[0].int().tolist()
        conf = float(box.conf[0])
        cls = int(box.cls[0])
        label = model.names[cls]

        color = (0, 255, 0)
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(image, f"{label} {conf:.2f}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    cv2.imshow("Detected Image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_objects("Sprite.jpg")
