import cv2
from pyzbar.pyzbar import decode
import numpy as np

image = cv2.imread('bring-scanner-800.jpg')

decoded_objects = decode(image)

for obj in decoded_objects:
    barcode_data = obj.data.decode('utf-8')
    barcode_type = obj.type
    print(f"Detected barcode: {barcode_data}")
    print(f"Barcode type: {barcode_type}")

    rect_points = obj.polygon

    if len(rect_points) == 4:
        points = np.array([(point.x, point.y) for point in rect_points], dtype=np.int32)
        points = points.reshape((-1, 1, 2))
        cv2.polylines(image, [points], isClosed=True, color=(0, 255, 0), thickness=3)

    elif len(rect_points) > 4:
        hull = cv2.convexHull(np.array([(point.x, point.y) for point in rect_points], dtype=np.float32))
        hull = hull.astype(np.int32)
        cv2.polylines(image, [hull], True, (0, 255, 0), 3)

    if rect_points:
        x, y = rect_points[0].x, rect_points[0].y
        cv2.putText(image, barcode_data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

# cv2.imshow("Barcode Reader", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
