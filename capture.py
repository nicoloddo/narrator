import imageio
from PIL import Image
import numpy as np
import os
import time

# Folder
folder = "frames"

# Create the frames folder if it doesn't exist
frames_dir = os.path.join(os.getcwd(), folder)
os.makedirs(frames_dir, exist_ok=True)

# Initialize the webcam
reader = imageio.get_reader('<video0>')

# Wait for the camera to initialize and adjust light levels
time.sleep(2)

try:
    while True:
        frame = reader.get_next_data()
        
        # Convert the frame to a PIL image
        pil_img = Image.fromarray(frame)

        # Resize the image
        max_size = 500
        ratio = max_size / max(pil_img.size)
        new_size = tuple([int(x*ratio) for x in pil_img.size])
        resized_img = pil_img.resize(new_size, Image.LANCZOS)

        # Save the frame as an image file
        print("📸 Say cheese! Saving frame.")
        path = os.path.join(frames_dir, "frame.jpg")
        resized_img.save(path)
        
        # Wait for 2 seconds
        time.sleep(2)
finally:
    reader.close()
