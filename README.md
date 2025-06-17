# Camera Timelapse Monitor

An automated Python script that captures images at regular intervals using OpenCV and uploads them to Google Drive for easy timelapse creation and remote monitoring.

## 🌐 Features

* **Automated Photography**: Captures high-quality images at configurable intervals
* **Google Drive Integration**: Automatically uploads images to organized folders
* **Smart Organization**: Creates date-based folders for easy navigation
* **Error Handling**: Robust retry logic and comprehensive logging
* **Configurable Settings**: Easily adjust capture intervals, image quality, and more
* **Graceful Shutdown**: Clean exit handling with proper resource cleanup

## 📋 Requirements

### Hardware

* Computer with camera (webcam, USB camera, or Raspberry Pi camera)
* Stable internet connection for Google Drive uploads

### Software

* Python 3.7+
* Camera compatible with OpenCV

## 🚀 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/camera-timelapse-monitor.git
   cd camera-timelapse-monitor
   ```

2. **Install dependencies**

   ```bash
   pip install opencv-python pydrive schedule
   ```

3. **Set up Google Drive API**

   * Go to [Google Cloud Console](https://console.cloud.google.com/)
   * Create a new project or select existing one
   * Enable the Google Drive API
   * Create credentials (OAuth 2.0 Client ID)
   * Download the credentials JSON file and rename it to `client_secrets.json`
   * Place it in the project directory

## ⚙️ Configuration

Edit the `CONFIG` dictionary in the script to customize settings:

```python
CONFIG = {
    'image_root': "captured_images",      # Local storage folder
    'capture_interval_seconds': 60,       # Time between captures (seconds)
    'camera_index': 0,                    # Camera device index
    'image_quality': 95,                  # JPEG quality (1-100)
    'warmup_time': 2,                     # Camera warmup time
    'max_retries': 3,                     # Upload retry attempts
}
```

### Common Settings:

* **Every minute**: `capture_interval_seconds: 60`
* **Every 5 minutes**: `capture_interval_seconds: 300`
* **Every hour**: `capture_interval_seconds: 3600`

## 🎯 Usage

1. **First Run** (Authentication)

   ```bash
   python camera_monitor.py
   ```

   * A browser window will open for Google Drive authentication
   * Grant permissions to access your Google Drive
   * Credentials will be saved for future runs

2. **Normal Operation**

   ```bash
   python camera_monitor.py
   ```

   * Script will start capturing images immediately
   * Press `Ctrl+C` to stop gracefully

## 📁 File Organization

### Local Storage

```
captured_images/
├── 2024-01-15/
│   ├── 20240115_090000.jpg
│   ├── 20240115_091000.jpg
│   └── ...
├── 2024-01-16/
│   └── ...
└── logs/
```

### Google Drive Structure

```
camera_timelapse_monitor/
├── 2024-01-15/
│   ├── 20240115_090000.jpg
│   ├── 20240115_091000.jpg
│   └── ...
└── 2024-01-16/
    └── ...
```

## 📊 Logging

The script creates detailed logs with timestamps:

* **Console output**: Real-time status updates
* **Log files**: `camera_monitor_YYYYMMDD.log` for each day
* **Log levels**: INFO, WARNING, ERROR for different events

## 🔧 Troubleshooting

### Camera Issues

* **Camera not found**: Check `camera_index` in config (try 0, 1, 2...)
* **Poor image quality**: Adjust `image_quality` and camera resolution settings
* **Camera busy**: Ensure no other applications are using the camera

### Google Drive Issues

* **Authentication failed**: Delete `mycreds.txt` and re-authenticate
* **Upload failures**: Check internet connection and Google Drive storage space
* **Permission errors**: Verify Google Drive API is enabled and credentials are correct

### Common Error Solutions

```bash
# If camera permission denied (Linux)
sudo usermod -a -G video $USER

# If OpenCV installation issues
pip install --upgrade pip
pip install opencv-python-headless

# For Raspberry Pi users
sudo apt-get update
sudo apt-get install python3-opencv
```

## 🎥 Creating Timelapses

Once you have collected images, you can create timelapses using:

### FFmpeg (Recommended)

```bash
ffmpeg -framerate 24 -pattern_type glob -i "captured_images/2024-01-*/*.jpg" -c:v libx264 -pix_fmt yuv420p camera_timelapse.mp4
```

### Python Script

```python
import cv2
import glob

# Get all images
images = sorted(glob.glob("captured_images/*/*.jpg"))

# Create video writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video = cv2.VideoWriter('timelapse.mp4', fourcc, 24, (1920, 1080))

for image_path in images:
    img = cv2.imread(image_path)
    video.write(img)

video.release()
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the log files for error details
3. Open an issue on GitHub with:

   * Your operating system
   * Python version
   * Complete error message
   * Steps to reproduce

---

**Enjoy your time-lapse creation! 🌟📷**
