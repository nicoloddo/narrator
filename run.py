import subprocess

def main():
    # Start capture.py
    capture_process = subprocess.Popen(['python', 'capture.py'])
    print("Webcam capture started...")

    # Start narrator.py
    narrator_process = subprocess.Popen(['python', 'narrator.py'])
    print("Narrator started...")

    try:
        # Wait for both processes to complete
        capture_process.wait()
        narrator_process.wait()
    except KeyboardInterrupt:
        # If interrupted, terminate both processes
        print("Interrupt received, stopping processes.")
        capture_process.terminate()
        narrator_process.terminate()
    finally:
        # Ensure all processes are terminated
        capture_process.wait()
        narrator_process.wait()
        print("Both processes have been terminated.")

if __name__ == "__main__":
    main()
