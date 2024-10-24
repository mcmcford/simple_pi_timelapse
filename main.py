import time
from picamera2 import Picamera2
from textual.app import App
from textual.widgets import Button, Log, Input, Label
from textual.containers import Horizontal, Vertical
from textual import on
import os
import threading

# Path to save captured images
# get the working directory
save_path = os.getcwd() + "/Photos"

# Create the directory if it doesn't exist
if not os.path.exists(save_path):
    os.makedirs(save_path)

# Initialize the Picamera2 object
camera = Picamera2()

# Configure the camera (optional: you can adjust these settings as needed)
camera_config = camera.create_still_configuration()
camera.configure(camera_config)
camera.start()  # Start the camera

class Settings:
    def __init__(self):
        self.running = False
        self.kill = False
        self.counter = 0
        self.worker = None
        self.fpm = 2
        self.gen_fps = 24


    def start(self):
        self.running = True

    def pause(self):
        self.running = False

    def stop(self):
        self.running = False
        self.kill = True

    def increment(self):
        self.counter += 1

SETTINGS = Settings()

class MyApp(App):

    CSS = """Select {
        margin: 1 2;
    }
    Label {
        margin: 1 2;
    }
    Button {
        margin: 1 2;
    }
    Log {
        margin: 0 2;
    }
    """


    def compose(self):
        # Create 3 buttons, "Start", "Pause" and "Stop"

        yield Vertical(
            Horizontal(
                Button("Start", id="start", variant="success"),
                Button("Pause", id="pause", variant="warning", disabled = True),
                Button("Stop", id="stop", variant="error"),
                Button("Generate", id="generate", variant="primary", disabled = True),
            ),
            Vertical(
                Label("Frames Per Minute:"),
                Input(placeholder="2", type="integer", id="fpm"),
                Log(id="log",  auto_scroll=True),
            )
        )

    @on(Input.Changed, "#fpm")
    def select_changed(self, event: Input.Changed) -> None:
        # ensure the input is an integer

        current_fpm = SETTINGS.fpm

        try:
            SETTINGS.fpm = int(event.value)
        except ValueError:
            SETTINGS.fpm = 2

        if current_fpm == SETTINGS.fpm:
            return

        current_time = time.strftime("%H:%M:%S")
        self.query_one("#log").write(f"{current_time} - FPM Updated from {current_fpm} to {SETTINGS.fpm}\n")

    @on(Button.Pressed, "#stop")
    def stop(self, event: Button.Pressed) -> None:
        self.stop_capture()

        current_time = time.strftime("%H:%M:%S")
        self.query_one("#log").write(f"{current_time} - Timelapse Stopped\n")
        self.query_one("#log").write(f"{current_time} - Total images captured: {SETTINGS.counter}\n")
        self.query_one("#log").write(f"{current_time} - Images saved in {save_path}\n")
        self.query_one("#log").write(f"{current_time} - WARNING: press the 'Start' button to start a new timelapse, overwriting the previous images\n")

        # disable the stop button
        event.button.disabled = True

        # disable the pause button
        pause_button = self.query_one("#pause")
        pause_button.disabled = True

        # enable the start button
        start_button = self.query_one("#start")
        start_button.disabled = False

        # rename the start button to start
        start_button.text = "Start"
        start_button.refresh()

        # reset the counter to 0
        SETTINGS.counter = 0

        # enable the generate button
        generate_button = self.query_one("#generate")
        generate_button.disabled = False

    @on(Button.Pressed, "#start")
    def start(self, event: Button.Pressed) -> None:
        # disable the start button
        event.button.disabled = True
        # enable the pause button
        pause_button = self.query_one("#pause")
        pause_button.disabled = False

        # rename the start button to resume
        event.button.label = "Resume"
        event.button.refresh()

        # get the time in the format HH:MM:SS
        current_time = time.strftime("%H:%M:%S")

        self.query_one("#log").write(f"{current_time} - Timelapse Started\n")

        self.start_capture()

    @on(Button.Pressed, "#pause")
    def pause(self, event: Button.Pressed) -> None:
        self.pause_capture()
        # disable the pause button
        event.button.disabled = True
        # enable the start button
        start_button = self.query_one("#start")
        start_button.disabled = False

        current_time = time.strftime("%H:%M:%S")

        self.query_one("#log").write(f"{current_time} - Timelapse Paused\n")
            
    @on(Button.Pressed, "#generate")
    def generate(self, event: Button.Pressed) -> None:
        self.generate_video()

    def start_capture(self):
        SETTINGS.start()

        # Create a worker thread to take pictures
        if SETTINGS.worker is None:
            SETTINGS.worker = threading.Thread(target=self.photographer)
            SETTINGS.worker.start()

    def pause_capture(self):
        SETTINGS.pause()

    def stop_capture(self):
        SETTINGS.stop()
        if SETTINGS.worker:
            SETTINGS.worker.join()
            SETTINGS.worker = None

    def generate_video(self):
        # use ffmpeg to generate a video
        video_path = os.getcwd()

        current_time = time.strftime("%H:%M:%S")
        self.query_one("#log").write(f"{current_time} - Starting timelapse generation\n")

        os.system(f"ffmpeg -hide_banner -loglevel error -framerate {SETTINGS.gen_fps} -i {save_path}/%d.jpg -c:v libx264 -profile:v high -crf 20 -pix_fmt yuv420p {video_path}/output.mp4")

        current_time = time.strftime("%H:%M:%S")
        self.query_one("#log").write(f"{current_time} - Timelapse generation completed\n")

    def photographer(self):

        time_slept = 0

        while True:
            if SETTINGS.kill:
                break
            if SETTINGS.running:

                # this stops button actions from hanging by having a 30 second sleep
                if time_slept < (60/SETTINGS.fpm):
                    time_slept += 1
                    time.sleep(1)
                    continue

                current_time = time.strftime("%H:%M:%S")
                self.query_one("#log").write(f"{current_time} - Capturing image {SETTINGS.counter}\n")
                # Capture an image using Picamera2
                file_name = os.path.join(save_path, f"{SETTINGS.counter}.jpg")
                camera.capture_file(file_name)
                SETTINGS.increment()
                print(f"Captured image {SETTINGS.counter}")
                time_slept = 0
                time.sleep(1) 
            else:
                time.sleep(1)

if __name__ == "__main__":
    app = MyApp()
    app.run()
