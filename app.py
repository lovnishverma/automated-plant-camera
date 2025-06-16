import cv2
import time
import os
import schedule
import logging
from datetime import datetime
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import signal
import sys

# -------------------- SETUP --------------------

# Setup logger with file output
log_filename = f"plant_monitor_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO, 
    format='[%(asctime)s] %(levelname)s: %(message)s', 
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

# Configuration
CONFIG = {
    'image_root': "captured_images",
    'capture_interval_seconds': 60,
    'camera_index': 0,
    'image_quality': 95,  # JPEG quality
    'warmup_time': 2,     # Camera warmup seconds
    'max_retries': 3,     # Upload retry attempts
}

# Global variables
drive = None
plants_folder_id = None
running = True

# -------------------- SIGNAL HANDLER --------------------

def signal_handler(sig, frame):
    global running
    logging.info(" Received shutdown signal. Cleaning up...")
    running = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# -------------------- GOOGLE DRIVE FUNCTIONS --------------------

def authenticate_drive():
    """Authenticate with Google Drive with error handling."""
    global drive, plants_folder_id
    
    try:
        logging.info(" Authenticating with Google Drive...")
        gauth = GoogleAuth()
        
        # Load existing credentials
        if os.path.exists("mycreds.txt"):
            gauth.LoadCredentialsFile("mycreds.txt")
        
        if gauth.credentials is None:
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            gauth.Refresh()
        else:
            gauth.Authorize()
            
        gauth.SaveCredentialsFile("mycreds.txt")
        drive = GoogleDrive(gauth)
        
        # Setup plants folder
        plants_folder_id = get_or_create_drive_folder("plants")
        logging.info(" Google Drive authentication successful")
        return True
        
    except Exception as e:
        logging.error(f" Google Drive authentication failed: {e}")
        return False

def get_or_create_drive_folder(name, parent_id=None):
    """Return ID of folder with given name. Create if not exists."""
    try:
        query = f"title='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        else:
            query += " and 'root' in parents"

        file_list = drive.ListFile({'q': query}).GetList()
        if file_list:
            return file_list[0]['id']

        # Create folder if not found
        folder_metadata = {'title': name, 'mimeType': 'application/vnd.google-apps.folder'}
        if parent_id:
            folder_metadata['parents'] = [{'id': parent_id}]
        folder = drive.CreateFile(folder_metadata)
        folder.Upload()
        logging.info(f" Created folder: {name}")
        return folder['id']
        
    except Exception as e:
        logging.error(f" Failed to create/get folder {name}: {e}")
        return None

# -------------------- CAMERA FUNCTIONS --------------------

def capture_image(filepath):
    """Capture image from camera with error handling."""
    cam = None
    try:
        logging.info(f" Attempting to capture image...")
        cam = cv2.VideoCapture(CONFIG['camera_index'])
        
        # Check if camera opened successfully
        if not cam.isOpened():
            logging.error(" Cannot open camera")
            return False
            
        # Set camera properties for better quality
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        
        # Allow camera to warm up
        time.sleep(CONFIG['warmup_time'])
        
        # Capture frame
        ret, frame = cam.read()
        
        if not ret or frame is None:
            logging.error(" Failed to capture frame")
            return False

        # Save with specified quality
        cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, CONFIG['image_quality']])
        
        # Verify file was created and has reasonable size
        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:  # At least 1KB
            logging.info(f" Image captured successfully: {os.path.basename(filepath)}")
            return True
        else:
            logging.error(" Image file not created or too small")
            return False
            
    except Exception as e:
        logging.error(f" Camera capture error: {e}")
        return False
    finally:
        if cam is not None:
            cam.release()

# -------------------- UPLOAD FUNCTIONS --------------------

def upload_with_retry(local_filepath, filename, day_folder_id, max_retries=None):
    """Upload file to Google Drive with retry logic."""
    if max_retries is None:
        max_retries = CONFIG['max_retries']
        
    for attempt in range(max_retries):
        try:
            file_drive = drive.CreateFile({
                'title': filename,
                'parents': [{'id': day_folder_id}]
            })
            file_drive.SetContentFile(local_filepath)
            file_drive.Upload()
            
            logging.info(f" Upload successful: {filename}")
            return True
            
        except Exception as e:
            logging.warning(f" Upload attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)  # Wait before retry
            else:
                logging.error(f" Upload failed after {max_retries} attempts")
                
    return False

# -------------------- MAIN FUNCTION --------------------

def capture_and_upload():
    """Main function to capture image and upload to Drive."""
    if not running:
        return
        
    # Prepare folder name and paths
    now = datetime.now()
    date_folder = now.strftime("%Y-%m-%d")
    filename = now.strftime("%Y%m%d_%H%M%S") + ".jpg"

    # Local folder path
    local_day_folder = os.path.join(CONFIG['image_root'], date_folder)
    os.makedirs(local_day_folder, exist_ok=True)
    local_filepath = os.path.join(local_day_folder, filename)

    # Capture image
    if not capture_image(local_filepath):
        return

    # Upload to Google Drive if authentication is successful
    if drive and plants_folder_id:
        # Create/get date folder in Drive
        day_folder_id = get_or_create_drive_folder(date_folder, parent_id=plants_folder_id)
        
        if day_folder_id:
            success = upload_with_retry(local_filepath, filename, day_folder_id)
            if success:
                logging.info(f" Total files in local folder: {len(os.listdir(local_day_folder))}")
        else:
            logging.error(" Could not create/access Drive folder")
    else:
        logging.warning(" Skipping upload - Drive not authenticated")

# -------------------- CLEANUP FUNCTION --------------------

def cleanup_old_files(days_to_keep=7):
    """Remove local files older than specified days."""
    # This could be scheduled to run daily
    # Implementation left as exercise - would check file dates and remove old ones
    pass

# -------------------- MAIN EXECUTION --------------------

def main():
    global running
    
    logging.info(" Plant Monitor Script Starting...")
    
    # Authenticate with Google Drive
    if not authenticate_drive():
        logging.error(" Cannot continue without Google Drive access")
        return
    
    # Setup scheduler
    schedule.every(CONFIG['capture_interval_seconds']).seconds.do(capture_and_upload)
    logging.info(f" Capturing image every {CONFIG['capture_interval_seconds']} seconds. Press Ctrl+C to stop.")
    
    # Take first image immediately
    capture_and_upload()

    # Main loop
    try:
        while running:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info(" Script stopped by user.")
    finally:
        logging.info(" Plant Monitor Script Ended.")

if __name__ == "__main__":
    main()