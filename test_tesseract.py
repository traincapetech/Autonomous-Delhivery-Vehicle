from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe" 

image_path = 'ss.png'
image = Image.open(image_path)

text = pytesseract.image_to_string(image)

print("Detected text:")
print(text)
