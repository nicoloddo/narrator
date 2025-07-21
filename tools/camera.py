import os
import asyncio
import base64
import errno
import io
import numpy as np
from PIL import Image
import imageio
import boto3
from datetime import datetime

import tools.audio_feedback as audio_feedback

MOVEMENT_DEFAULT_THRESHOLD = 4


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
            f"Instantiating camera with thresholds: {darkness_threshold}, {hue_uniformity_threshold}, {saturation_uniformity_threshold}, movement: {movement_threshold}"
        )
        self.frames_dir = frames_dir
        self.darkness_threshold = int(darkness_threshold)

        # S3 configuration
        self.use_s3 = os.environ.get("USE_S3_STORAGE", "false").lower() == "true"
        self.s3_bucket = os.environ.get("S3_BUCKET_NAME")
        self.s3_prefix = os.environ.get("S3_KEY_PREFIX", "narrator-frames")

        if self.use_s3:
            if not self.s3_bucket:
                raise ValueError(
                    "S3_BUCKET_NAME environment variable is required when USE_S3_STORAGE=true"
                )

            try:
                self.s3_client = boto3.client("s3")
                print(
                    f"🪣 S3 storage enabled: bucket={self.s3_bucket}, prefix={self.s3_prefix}"
                )
            except Exception as e:
                print(f"Failed to initialize S3 client: {e}")
                print("Falling back to local storage")
                self.use_s3 = False
        else:
            self.s3_client = None
            print(f"💾 Local storage enabled: {frames_dir}")
        self.hue_uniformity_threshold = int(hue_uniformity_threshold)
        self.saturation_uniformity_threshold = int(saturation_uniformity_threshold)
        self.movement_threshold = (
            int(movement_threshold)
            if movement_threshold is not None
            else MOVEMENT_DEFAULT_THRESHOLD
        )
        self.previous_frame = None  # Store previous frame for movement detection
        os.makedirs(self.frames_dir, exist_ok=True)
        print(f"Camera instantiated.")

    async def get_camera(self, camera="<video0>"):
        """Async version of camera initialization."""
        while True:
            try:
                reader = imageio.get_reader(camera)
                return reader
            except IOError:
                # Wait a bit and retry (non-blocking)
                await asyncio.sleep(0.1)

    async def encode_image(self, image_path):
        """Async version of image encoding."""
        while True:
            try:
                # Run file I/O in executor to avoid blocking
                loop = asyncio.get_running_loop()
                with open(image_path, "rb") as image_file:
                    image_data = await loop.run_in_executor(None, image_file.read)
                    return base64.b64encode(image_data).decode("utf-8")
            except IOError as e:
                if e.errno != errno.EACCES:
                    # Not a "file in use" error, re-raise
                    raise
                # File is being written to, wait a bit and retry (non-blocking)
                await asyncio.sleep(0.1)

    async def capture(self, reader, *, debugging=False):
        """Async version of frame capture."""
        if debugging:
            print("Started camera debugging")

        is_dark_or_uniform = True
        count_frames = 0

        while is_dark_or_uniform or debugging:
            # Get frame in executor to avoid blocking if needed
            loop = asyncio.get_running_loop()
            frame = await loop.run_in_executor(None, reader.get_next_data)

            # Process frame (CPU-bound, run in executor)
            img_str, is_dark_or_uniform = await loop.run_in_executor(
                None, self._process_frame, frame, count_frames, debugging
            )

            if count_frames % self.PRINT_DEBUG_EACH_N_FRAMES == 0:
                if is_dark_or_uniform:
                    print("I can't see...")
                    audio_feedback.cant_see()
                    print()
                elif debugging:
                    print("I can see clear!")
                    print()
                    audio_feedback.i_see()

            # Count frames for debugging prints
            count_frames += 1
            if count_frames == self.PRINT_DEBUG_EACH_N_FRAMES + 1:
                count_frames = 0

        # We are out of the loop, so the image is ok
        return img_str

    async def capture_movement(self, reader, *, debugging=False):
        """
        Async version of movement detection capture.
        Capture frames from the camera until movement is detected.
        Returns the base64 encoded image when movement is found.
        """
        if debugging:
            print("Started movement detection")

        movement_detected = False
        count_frames = 0

        while not movement_detected or debugging:
            # Get frame in executor to avoid blocking if needed
            loop = asyncio.get_running_loop()
            frame = await loop.run_in_executor(None, reader.get_next_data)

            # Process frame and detect movement (CPU-bound, run in executor)
            img_str, movement_detected = await loop.run_in_executor(
                None, self._process_movement_frame, frame, count_frames, debugging
            )

            if debugging and (
                count_frames % self.PRINT_DEBUG_EACH_N_FRAMES == 0 or movement_detected
            ):
                if movement_detected:
                    print("Movement detected!")
                    audio_feedback.i_see()
                else:
                    print("No movement detected...")
                    audio_feedback.cant_see()
                print()

            # Count frames for debugging prints
            count_frames += 1
            if count_frames == self.PRINT_DEBUG_EACH_N_FRAMES + 1:
                count_frames = 0

            # Small delay to avoid overwhelming the system (non-blocking)
            if not movement_detected:
                await asyncio.sleep(1)

        # Movement detected! Save the frame and return
        print("✨ Movement captured!")
        return img_str

    def _process_frame(self, frame, count_frames, debugging):
        """
        Process a single frame (synchronous, meant to run in executor).
        Returns tuple of (img_str, is_dark_or_uniform).
        """
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

        # Check image quality
        is_dark_or_uniform = self._check_image_quality(
            resized_img, count_frames, debugging
        )

        # Save the frame if it's good quality
        if not is_dark_or_uniform:
            filename = f"frame_{count_frames}.jpg"
            self.save_frame(resized_img, filename)

        return img_str, is_dark_or_uniform

    def _process_movement_frame(self, frame, count_frames, debugging):
        """
        Process a single frame for movement detection (synchronous, meant to run in executor).
        Returns tuple of (img_str, movement_detected).
        """
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
        movement_detected = self._detect_movement(resized_img, count_frames, debugging)

        # Store current frame as previous for next iteration
        self.previous_frame = resized_img.copy()

        # Save frame if movement detected
        if movement_detected:
            filename = f"movement_frame_{count_frames}.jpg"
            self.save_frame(resized_img, filename)

        return img_str, movement_detected

    def _check_image_quality(self, image, count_frames, debugging=False):
        """Check if image is too dark or lacks color variance (synchronous)."""
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
        Detect movement by comparing current frame with previous frame (synchronous).
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

        if debugging and (
            count_frames % self.PRINT_DEBUG_EACH_N_FRAMES == 0
            or mean_diff > self.movement_threshold
        ):
            print(
                f"Movement difference: {mean_diff:.2f} (threshold: {self.movement_threshold})"
            )

        # Return True if movement exceeds threshold
        return mean_diff > self.movement_threshold

    def save_frame(self, frame, filename):
        """Save a frame to S3 or local filesystem."""
        if self.use_s3 and self.s3_client:
            try:
                # Create a BytesIO buffer to store the image
                img_buffer = io.BytesIO()
                frame.save(img_buffer, format="JPEG", quality=85)
                img_buffer.seek(0)

                # Create S3 key with timestamp and prefix
                timestamp = datetime.now().strftime("%Y/%m/%d/%H")
                s3_key = f"{self.s3_prefix}/{timestamp}/{filename}"

                # Upload to S3
                self.s3_client.upload_fileobj(
                    img_buffer,
                    self.s3_bucket,
                    s3_key,
                    ExtraArgs={
                        "ContentType": "image/jpeg",
                        "Metadata": {
                            "source": "narrator-camera",
                            "timestamp": datetime.now().isoformat(),
                        },
                    },
                )
                print(f"📤 Frame saved to S3: s3://{self.s3_bucket}/{s3_key}")

            except Exception as e:
                print(f"❌ Failed to save frame to S3: {e}")
                print("🔄 Falling back to local storage")
                # Fall back to local storage
                self._save_frame_locally(frame, filename)
        else:
            # Save locally
            self._save_frame_locally(frame, filename)

    def _save_frame_locally(self, frame, filename):
        """Save a frame to local filesystem."""
        path = os.path.join(self.frames_dir, filename)
        frame.save(path)
        print(f"💾 Frame saved locally: {path}")
