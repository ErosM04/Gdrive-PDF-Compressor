import shutil
import os


def clean_directory(directory):
        """Removes the given direcory and its content."""
        print(f"Removing '{directory}' folder...")
        
        if os.path.exists(directory):
            shutil.rmtree(directory)

        print("Folder removed")


def format_duration(duration):
    "Formats a number into ``xxh xxm xxs``"
    duration = int(duration)
    if duration < 60:
        return f"{duration}s"
    elif duration < 3600:
        minutes = int(duration // 60)
        seconds = duration % 60
        return f"{minutes}m {seconds}s"
    else:
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = duration % 60
        return f"{hours}h {minutes}m {seconds}s"