import os
import time
import base64
import errno
import io
import numpy as np
from PIL import Image
import imageio

import audio_feedback


class Camera:
    PRINT_DEBUG_EACH_N_FRAMES = 50

    def __init__(
        self,
        frames_dir,
        darkness_threshold,
        hue_uniformity_threshold,
        saturation_uniformity_threshold,
        movement_threshold=None,
    ):
        print(
            f"Initializing camera with thresholds: {darkness_threshold}, {hue_uniformity_threshold}, {saturation_uniformity_threshold}, movement: {movement_threshold}"
        )
        self.frames_dir = frames_dir
        self.darkness_threshold = int(darkness_threshold)
        self.hue_uniformity_threshold = int(hue_uniformity_threshold)
        self.saturation_uniformity_threshold = int(saturation_uniformity_threshold)
        self.movement_threshold = (
            int(movement_threshold) if movement_threshold is not None else 10
        )
        self.previous_frame = None  # Store previous frame for movement detection
        os.makedirs(self.frames_dir, exist_ok=True)
        print(f"Camera initialized.")

    def get_camera(self, camera="<video0>"):
        while True:
            try:
                reader = imageio.get_reader(camera)
                return reader
            except IOError:
                # Wait a bit and retry
                time.sleep(0.1)

    def encode_image(self, image_path):
        while True:
            try:
                with open(image_path, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode("utf-8")
            except IOError as e:
                if e.errno != errno.EACCES:
                    # Not a "file in use" error, re-raise
                    raise
                # File is being written to, wait a bit and retry
                time.sleep(0.1)

    def capture(self, reader, *, debugging=False):
        if debugging:
            print("Started camera debugging")

        is_dark_or_uniform = True

        count_frames = 0
        while is_dark_or_uniform or debugging:
            frame = reader.get_next_data()

            # Convert the frame to a PIL image
            pil_img = Image.fromarray(frame)

            # Resize the image
            max_size = 500
            ratio = max_size / max(pil_img.size)
            new_size = tuple([int(x * ratio) for x in pil_img.size])
            resized_img = pil_img.resize(new_size, Image.LANCZOS)

            # Convert PIL image to a bytes buffer and encode in base64
            buffered = io.BytesIO()
            resized_img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

            is_dark_or_uniform = self._check_image_quality(
                resized_img, count_frames, debugging
            )

            if debugging and count_frames % self.PRINT_DEBUG_EACH_N_FRAMES == 0:
                if is_dark_or_uniform:
                    print("I can't see...")
                    audio_feedback.cant_see()
                else:
                    print("I can see clear!")
                    audio_feedback.i_see()
                print()

            # Count frames for debugging prints
            count_frames += 1
            if count_frames == self.PRINT_DEBUG_EACH_N_FRAMES + 1:
                count_frames = 0

        # We are out of the loop, so the image is ok:
        # Save the frame as an image file for debugging purposes
        path = os.path.join(self.frames_dir, "frame.jpg")
        resized_img.save(path)
        return img_str

    def capture_movement(self, reader, *, debugging=False):
        """
        Capture frames from the camera until movement is detected.
        Returns the base64 encoded image when movement is found.
        """
        if debugging:
            print("Started movement detection")

        movement_detected = False
        count_frames = 0

        while not movement_detected:
            frame = reader.get_next_data()

            # Convert the frame to a PIL image
            pil_img = Image.fromarray(frame)

            # Resize the image (same as capture method)
            max_size = 500
            ratio = max_size / max(pil_img.size)
            new_size = tuple([int(x * ratio) for x in pil_img.size])
            resized_img = pil_img.resize(new_size, Image.LANCZOS)

            # Convert PIL image to a bytes buffer and encode in base64
            buffered = io.BytesIO()
            resized_img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

            # Check for movement
            movement_detected = self._detect_movement(
                resized_img, count_frames, debugging
            )

            if debugging and count_frames % self.PRINT_DEBUG_EACH_N_FRAMES == 0:
                if movement_detected:
                    print("Movement detected!")
                    audio_feedback.i_see()
                else:
                    print("No movement detected...")
                    audio_feedback.cant_see()
                print()

            # Store current frame as previous for next iteration
            self.previous_frame = resized_img.copy()

            # Count frames for debugging prints
            count_frames += 1
            if count_frames == self.PRINT_DEBUG_EACH_N_FRAMES + 1:
                count_frames = 0

            # Small delay to avoid overwhelming the system
            if not movement_detected:
                time.sleep(0.1)

        # Movement detected! Save the frame and return
        path = os.path.join(self.frames_dir, "movement_frame.jpg")
        resized_img.save(path)
        print("✨ Movement captured!")
        return img_str

    def _check_image_quality(self, image, count_frames, debugging=False):
        # Convert to grayscale and check brightness
        gray_image = image.convert("L")
        average_intensity = np.array(gray_image).mean()

        # Convert to HSV and check color uniformity
        hsv_image = image.convert("HSV")
        hsv_array = np.array(hsv_image)

        hue_std = hsv_array[:, :, 0].std()  # Standard deviation of the hue channel
        sat_std = hsv_array[
            :, :, 1
        ].std()  # Standard deviation of the saturation channel

        if debugging and count_frames % self.PRINT_DEBUG_EACH_N_FRAMES == 0:
            print(f"Hue std: {hue_std}")
            print(f"Sat std: {sat_std}")
            print(f"Brightness intensity: {average_intensity}")

        # Determine if the image is dark or lacks color variance
        is_dark = average_intensity < self.darkness_threshold
        lacks_color_variance = (
            sat_std < self.saturation_uniformity_threshold
            or hue_std < self.hue_uniformity_threshold
        )

        return is_dark or lacks_color_variance

    def _detect_movement(self, current_image, count_frames, debugging=False):
        """
        Detect movement by comparing current frame with previous frame.
        Returns True if movement is detected, False otherwise.
        """
        # If no previous frame, initialize it and return False
        if self.previous_frame is None:
            self.previous_frame = current_image.copy()
            return False

        # Convert both images to grayscale for comparison
        current_gray = current_image.convert("L")
        previous_gray = self.previous_frame.convert("L")

        # Convert to numpy arrays
        current_array = np.array(current_gray, dtype=np.float32)
        previous_array = np.array(previous_gray, dtype=np.float32)

        # Calculate absolute difference
        diff = np.abs(current_array - previous_array)

        # Calculate mean difference
        mean_diff = diff.mean()

        if debugging and count_frames % self.PRINT_DEBUG_EACH_N_FRAMES == 0:
            print(
                f"Movement difference: {mean_diff:.2f} (threshold: {self.movement_threshold})"
            )

        # Return True if movement exceeds threshold
        return mean_diff > self.movement_threshold
