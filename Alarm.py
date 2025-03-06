import time
import threading
from datetime import datetime
from tkinter import ttk, messagebox, filedialog
import pygame
import requests
import random
import json
import os
from PIL import Image, ImageTk
import tkinter as tk


class WeatherAlarmClock:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather Alarm Clock")
        self.root.geometry("800x600")
        self.root.configure(bg="#E3F2FD")

        # Initialize pygame for sound
        pygame.mixer.init()

        # Add alarm state tracking
        self.alarm_triggered = False
        self.alarm_thread = None

        # Create sounds directory and add default sounds
        os.makedirs("sounds", exist_ok=True)
        os.makedirs("user_sounds", exist_ok=True)

        # Default alarm sound paths
        self.default_sounds = {
            "Gentle Morning": "sounds/gentle_morning.mp3",
            "Wake Up Call": "sounds/wake_up.mp3",
            "Birds Chirping": "sounds/birds.mp3",
            "Ocean Waves": "sounds/ocean.mp3",
            "Rainfall": "sounds/rain.mp3"
        }
        self.selected_sound = "Gentle Morning"

        # Weather API config
        self.api_key = "b1690b6d937fd41b3fbaadaf85953edb"  # Replace with your OpenWeatherMap API key
        self.user_location = " "  # Default location

        # Motivational quotes
        self.quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "It always seems impossible until it's done. - Nelson Mandela",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
            "Don't watch the clock; do what it does. Keep going. - Sam Levenson",
            "The secret of getting ahead is getting started. - Mark Twain"
        ]

        # Initialize style configurations
        self.setup_styles()

        # Create main frames
        self.create_header_frame()
        self.create_alarm_frame()
        self.create_weather_frame()
        self.create_controls_frame()

        # Start clock update
        self.update_clock()

        # Initially fetch weather
        self.get_weather()

    def setup_styles(self):
        style = ttk.Style()

        # Configure main styles with vibrant colors
        style.configure("TFrame", background="#E3F2FD")
        style.configure("TLabelframe", background="#E3F2FD")
        style.configure("TLabelframe.Label",
                        font=("Helvetica", 11, "bold"),
                        foreground="#1976D2",
                        background="#E3F2FD")

        # Configure button styles
        style.configure("Accent.TButton",
                        font=("Helvetica", 10, "bold"),
                        background="#2196F3",
                        foreground="#FFFFFF")

        style.configure("TButton",
                        font=("Helvetica", 10),
                        background="#64B5F6")

        # Configure label styles
        style.configure("TLabel",
                        background="#E3F2FD",
                        font=("Helvetica", 10))

        # Configure combobox styles
        style.configure("TCombobox",
                        background="#BBDEFB",
                        fieldbackground="#FFFFFF")

    def create_header_frame(self):
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=20, pady=10)

        # Current time display with vibrant color
        self.clock_label = ttk.Label(
            header_frame,
            font=("Helvetica", 48, "bold"),
            foreground="#1565C0"  # Deeper blue for contrast
        )
        self.clock_label.pack(pady=10)

        # Quote display with styled text
        self.quote_label = ttk.Label(
            header_frame,
            font=("Helvetica", 12, "italic"),
            foreground="#0D47A1",  # Dark blue for quotes
            wraplength=700
        )
        self.quote_label.pack(pady=5)
        self.update_quote()

    def create_alarm_frame(self):
        alarm_frame = ttk.LabelFrame(self.root, text="⏰ Alarm Settings")
        alarm_frame.pack(fill="x", padx=20, pady=10)

        # Time selection
        time_frame = ttk.Frame(alarm_frame)
        time_frame.pack(pady=10)

        ttk.Label(time_frame, text="Hour:").grid(row=0, column=0, padx=5)
        self.hour_var = tk.StringVar(value="07")
        self.hour_combo = ttk.Combobox(
            time_frame,
            textvariable=self.hour_var,
            values=[str(h).zfill(2) for h in range(24)],
            width=5
        )
        self.hour_combo.grid(row=0, column=1, padx=5)

        ttk.Label(time_frame, text="Minute:").grid(row=0, column=2, padx=5)
        self.minute_var = tk.StringVar(value="00")
        self.minute_combo = ttk.Combobox(
            time_frame,
            textvariable=self.minute_var,
            values=[str(m).zfill(2) for m in range(60)],
            width=5
        )
        self.minute_combo.grid(row=0, column=3, padx=5)

        # Sound selection
        sound_frame = ttk.Frame(alarm_frame)
        sound_frame.pack(pady=10)

        ttk.Label(sound_frame, text="Alarm Sound:").pack(side="left", padx=5)
        self.sound_var = tk.StringVar(value=self.selected_sound)
        self.sound_combo = ttk.Combobox(
            sound_frame,
            textvariable=self.sound_var,
            values=list(self.default_sounds.keys()),
            width=20
        )
        self.sound_combo.pack(side="left", padx=5)

        ttk.Button(
            sound_frame,
            text="Test Sound",
            command=self.test_sound
        ).pack(side="left", padx=5)

        ttk.Button(
            sound_frame,
            text="Add Custom Sound",
            command=self.add_custom_sound
        ).pack(side="left", padx=5)

    def create_weather_frame(self):
        weather_frame = ttk.LabelFrame(self.root, text="🌤 Weather Information")
        weather_frame.pack(fill="x", padx=20, pady=10)

        # Location entry
        location_frame = ttk.Frame(weather_frame)
        location_frame.pack(pady=10)

        ttk.Label(location_frame, text="Location:").pack(side="left", padx=5)
        self.location_var = tk.StringVar(value=self.user_location)
        ttk.Entry(
            location_frame,
            textvariable=self.location_var,
            width=30
        ).pack(side="left", padx=5)

        ttk.Button(
            location_frame,
            text="Update Weather",
            command=self.update_location
        ).pack(side="left", padx=5)

        # Weather display
        self.weather_info = ttk.Label(
            weather_frame,
            font=("Helvetica", 12),
            wraplength=700
        )
        self.weather_info.pack(pady=10)

        self.weather_recommendation = ttk.Label(
            weather_frame,
            font=("Helvetica", 12),
            wraplength=700
        )
        self.weather_recommendation.pack(pady=10)

    def create_controls_frame(self):
        controls_frame = ttk.Frame(self.root)
        controls_frame.pack(fill="x", padx=20, pady=10)

        self.set_button = ttk.Button(
            controls_frame,
            text="Set Alarm",
            command=self.set_alarm,
            style="Accent.TButton"
        )
        self.set_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(
            controls_frame,
            text="Stop Alarm",
            command=self.stop_alarm,
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=5)

        self.alarm_status = ttk.Label(
            controls_frame,
            font=("Helvetica", 12, "bold"),
            foreground="#2c3e50"
        )
        self.alarm_status.pack(side="left", padx=20)

    def update_clock(self):
        current_time = datetime.now().strftime("%H:%M:%S")
        self.clock_label.config(text=current_time)

        # Check alarm
        if hasattr(self, 'alarm_active') and self.alarm_active:
            alarm_time = f"{self.hour_var.get()}:{self.minute_var.get()}"
            current_time_hm = datetime.now().strftime("%H:%M")

            # Check if alarm should trigger
            if alarm_time == current_time_hm and not self.alarm_triggered:
                self.alarm_triggered = True
                self.trigger_alarm()
        else:
            self.alarm_triggered = False

        self.root.after(1000, self.update_clock)

    def update_quote(self):
        self.quote_label.config(text=random.choice(self.quotes))

    def set_alarm(self):
        hour = self.hour_var.get()
        minute = self.minute_var.get()

        if not hour or not minute:
            messagebox.showerror("Error", "Please select a valid time")
            return

        self.alarm_active = True
        self.alarm_triggered = False
        self.selected_sound = self.sound_var.get()

        alarm_time = f"{hour.zfill(2)}:{minute.zfill(2)}"
        self.alarm_status.config(
            text=f"⏰ Alarm set for {alarm_time}",
            foreground="#00C853"  # Vibrant green for active alarm
        )

        self.set_button.config(state="disabled")
        self.stop_button.config(state="normal")

        messagebox.showinfo(
            "Alarm Set",
            f"Alarm has been set for {alarm_time}"
        )

    def stop_alarm(self):
        self.alarm_active = False
        self.alarm_triggered = False
        self.alarm_status.config(
            text="No alarm set",
            foreground="#FF5252"  # Red for no alarm
        )

        self.set_button.config(state="normal")
        self.stop_button.config(state="disabled")

        if pygame.mixer.get_busy():
            pygame.mixer.music.stop()

        # Stop the alarm thread if it's running
        if self.alarm_thread and self.alarm_thread.is_alive():
            self.alarm_thread = None

    def trigger_alarm(self):
        # Stop any existing alarm sound
        if pygame.mixer.get_busy():
            pygame.mixer.music.stop()

        # Create and start a new thread for playing the alarm
        self.alarm_thread = threading.Thread(
            target=self.play_alarm,
            daemon=True
        )
        self.alarm_thread.start()

        # Show notification with weather info
        weather_info = self.weather_info.cget("text")
        quote = self.quote_label.cget("text")

        # Schedule the notification to appear after a short delay
        self.root.after(100, lambda: messagebox.showinfo(
            "Wake Up!",
            f"Good Morning!\n\n{weather_info}\n\n{quote}"
        ))

    def play_alarm(self):
        sound_path = self.default_sounds.get(self.selected_sound)
        if not sound_path or not os.path.exists(sound_path):
            messagebox.showerror("Error", "Alarm sound file not found")
            return

        try:
            # Initialize mixer if not already initialized
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.set_volume(0.7)
            pygame.mixer.music.play(-1)  # Loop indefinitely

            # Play until stopped or 60 seconds have passed
            start_time = time.time()
            while (pygame.mixer.music.get_busy() and
                   time.time() - start_time < 60 and
                   self.alarm_active):
                pygame.time.Clock().tick(10)  # Reduce CPU usage

            pygame.mixer.music.stop()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not play alarm sound: {e}"
            )

    def test_sound(self):
        sound_path = self.default_sounds.get(self.sound_var.get())
        if not sound_path or not os.path.exists(sound_path):
            messagebox.showerror("Error", "Sound file not found")
            return

        if pygame.mixer.get_busy():
            pygame.mixer.stop()

        try:
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.set_volume(0.7)
            pygame.mixer.music.play()

            # Play for 5 seconds
            time.sleep(5)
            pygame.mixer.music.stop()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not play test sound: {e}"
            )

    def add_custom_sound(self):
        file_path = filedialog.askopenfilename(
            title="Select Alarm Sound",
            filetypes=[("Audio Files", "*.mp3 *.wav")]
        )

        if file_path:
            sound_name = os.path.basename(file_path).split('.')[0]
            new_path = os.path.join("user_sounds", os.path.basename(file_path))

            try:
                with open(file_path, 'rb') as src, open(new_path, 'wb') as dst:
                    dst.write(src.read())

                self.default_sounds[sound_name] = new_path
                self.sound_combo['values'] = list(self.default_sounds.keys())
                messagebox.showinfo(
                    "Success",
                    f"Added sound: {sound_name}"
                )
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Could not add sound: {e}"
                )

    def get_weather(self):
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={self.user_location}&appid={self.api_key}&units=metric"
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200:
                temp = data['main']['temp']
                feels_like = data['main']['feels_like']
                humidity = data['main']['humidity']
                description = data['weather'][0]['description']
                wind_speed = data['wind']['speed']

                weather_text = (
                    f"Current Weather in {self.user_location}:\n"
                    f"Temperature: {temp}°C (Feels like: {feels_like}°C)\n"
                    f"Condition: {description.capitalize()}\n"
                    f"Humidity: {humidity}%\n"
                    f"Wind Speed: {wind_speed} m/s"
                )
                self.weather_info.config(text=weather_text)

                # Generate recommendations
                self.generate_recommendations(
                    temp, description, humidity, wind_speed
                )
            else:
                self.weather_info.config(text="Weather data unavailable")
                self.weather_recommendation.config(text="")
        except Exception as e:
            self.weather_info.config(
                text="Error retrieving weather information"
            )
            self.weather_recommendation.config(text="")

    def generate_recommendations(self, temp, description, humidity, wind_speed):
        recommendation = "Today's Weather Recommendations:\n"

        # Temperature recommendations
        if temp < 5:
            recommendation += "• Bundle up with warm layers\n"
            recommendation += "• Wear a hat and gloves\n"
        elif temp < 15:
            recommendation += "• Wear a jacket or coat\n"
        elif temp < 25:
            recommendation += "• Comfortable temperature for light clothing\n"
        else:
            recommendation += "• Wear light, breathable clothing\n"
            recommendation += "• Stay hydrated\n"

        # Weather condition recommendations
        description = description.lower()
        if "rain" in description:
            recommendation += "• Bring an umbrella\n"
            recommendation += "• Wear waterproof shoes\n"
        elif "snow" in description:
            recommendation += "• Wear warm, waterproof boots\n"
            recommendation += "• Be careful of slippery conditions\n"
        elif "clear" in description and temp > 20:
            recommendation += "• Apply sunscreen\n"
            recommendation += "• Bring sunglasses\n"

        self.weather_recommendation.config(text=recommendation)

    def update_location(self):
        new_location = self.location_var.get()
        if new_location:
            self.user_location = new_location
            self.get_weather()


if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherAlarmClock(root)
    root.mainloop()