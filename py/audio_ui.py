# audio_ui.py
import flet as ft
from audio_computer import ESPListener, main as audio_main, stop_capture, turn_off_leds
import threading

def main(page: ft.Page):
    page.title = "Audio Visualizer Control"
    page.window_width = 600
    page.window_height = 400
    
    # Create global variables for control
    running = False
    audio_thread = None
    current_effect = 0  # 0 for LOFI, 1 for SPEED, 2 for FUNK
    esp_listener = ESPListener()  # Create ESP listener instance
    
    def get_current_effect():
        return current_effect
    
    def effect_changed(e):
        nonlocal current_effect
        if e.control.value == "speed":
            current_effect = 1
        elif e.control.value == "rainbow":
            current_effect = 2
        elif e.control.value == "snake":
            current_effect = 3
        elif e.control.value == "scroll":  # New condition
            current_effect = 4
        else:  # lofi
            current_effect = 0
        print(f"Selected effect: {e.control.value} ({current_effect})")
        status_text.value = f"Running... ({e.control.value} effect)" if running else "Stopped"
        page.update()
    
    # Update radio group
    effects_group = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="lofi", label="LoFi"),
            ft.Radio(value="scroll", label="LoFi 2"),  
            ft.Radio(value="speed", label="Speed"),
            ft.Radio(value="rainbow", label="Waves"),
            ft.Radio(value="snake", label="Waves outside"),
            # New option
        ]),
        value="lofi",  # Default effect
        on_change=effect_changed
    )
    
    def start_audio(e):
        nonlocal running, audio_thread
        if not running:
            running = True
            start_btn.disabled = True
            stop_btn.disabled = False
            status_text.value = f"Running... ({effects_group.value} effect)"
            page.update()
            
            # Pass get_current_effect function
            audio_thread = threading.Thread(
                target=lambda: audio_main(effect_getter=get_current_effect)
            )
            audio_thread.daemon = True
            audio_thread.start()
    
    def stop_audio(e):
        nonlocal running, audio_thread
        if running:
            running = False
            stop_capture()
            turn_off_leds(esp_listener)  # Turn off LEDs
            start_btn.disabled = False
            stop_btn.disabled = True
            status_text.value = "Stopped"
            page.update()
    
    # Create UI controls
    title = ft.Text("Audio Visualizer Control", size=24, weight=ft.FontWeight.BOLD)
    status_text = ft.Text("Stopped", size=16)
    
    start_btn = ft.ElevatedButton(
        text="Start",
        on_click=start_audio,
        style=ft.ButtonStyle(
            color={ft.MaterialState.DEFAULT: ft.colors.WHITE},
            bgcolor={ft.MaterialState.DEFAULT: ft.colors.GREEN}
        )
    )
    
    stop_btn = ft.ElevatedButton(
        text="Stop",
        on_click=stop_audio,
        disabled=True,
        style=ft.ButtonStyle(
            color={ft.MaterialState.DEFAULT: ft.colors.WHITE},
            bgcolor={ft.MaterialState.DEFAULT: ft.colors.RED}
        )
    )
    
    # Layout
    controls = ft.Row(
        controls=[start_btn, stop_btn],
        alignment=ft.MainAxisAlignment.CENTER
    )
    
    page.add(
        ft.Column(
            controls=[
                title,
                status_text,
                effects_group,  # Add effects selection
                controls
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )
    )

if __name__ == "__main__":
    ft.app(target=main)