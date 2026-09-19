import time
import sys
import glob
import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

def cleanup_pilot_test_records():
    for f in glob.glob("artifacts/ml/defect_annotations/records/*.json"):
        try:
            with open(f, "r") as fp:
                d = json.load(fp)
            if "pilot" in d.get("image_id", ""):
                os.remove(f)
                print(f"Cleaned up test record: {f}")
        except Exception:
            pass

def run_test():
    cleanup_pilot_test_records()
    
    options = Options()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")
    
    service = Service(executable_path="/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    try:
        url = "http://localhost:5173/internal/annotation"
        print(f"Navigating to {url}...")
        driver.get(url)
        time.sleep(2)
        
        # Clear sessionStorage to ensure clean starting test state
        driver.execute_script("sessionStorage.clear();")
        driver.refresh()
        time.sleep(2)
        
        wait = WebDriverWait(driver, 10)
        
        # Step 1: Verify Image 1
        counter_el = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Image ') and contains(., ' of 10')]")))
        print(f"Initial counter text: {counter_el.text}")
        assert "Image 1 of 10" in counter_el.text, f"Expected Image 1 of 10, got {counter_el.text}"
        
        # Select 'Healthy' on Image 1
        healthy_btn = wait.until(EC.element_to_be_clickable((By.ID, "label-healthy-btn")))
        healthy_btn.click()
        time.sleep(0.5)
        
        # Click SAVE & NEXT IMAGE
        save_btn = wait.until(EC.element_to_be_clickable((By.ID, "save-next-btn")))
        save_btn.click()
        time.sleep(1)
        
        # Verify NO alert popup appeared
        try:
            alert = driver.switch_to.alert
            alert_text = alert.text
            alert.accept()
            raise AssertionError(f"Unexpected alert popup appeared: {alert_text}")
        except Exception as e:
            if "Unexpected alert popup" in str(e):
                raise
            # Normal: no alert is expected
        
        time.sleep(1)
        
        # Step 2: Verify Image 2
        counter_el = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Image ') and contains(., ' of 10')]")))
        print(f"After Image 1 save, counter text: {counter_el.text}")
        assert "Image 2 of 10" in counter_el.text, f"Expected Image 2 of 10, got {counter_el.text}"
        
        # Select 'Damaged' on Image 2
        damage_btn = wait.until(EC.element_to_be_clickable((By.ID, "label-damage-btn")))
        damage_btn.click()
        time.sleep(0.5)
        
        # Click SAVE & NEXT IMAGE
        save_btn = wait.until(EC.element_to_be_clickable((By.ID, "save-next-btn")))
        save_btn.click()
        time.sleep(1)
        
        # Verify NO alert popup appeared
        try:
            alert = driver.switch_to.alert
            alert_text = alert.text
            alert.accept()
            raise AssertionError(f"Unexpected alert popup appeared: {alert_text}")
        except Exception as e:
            if "Unexpected alert popup" in str(e):
                raise
                
        time.sleep(1)
        
        # Step 3: Verify Image 3
        counter_el = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Image ') and contains(., ' of 10')]")))
        print(f"After Image 2 save, counter text: {counter_el.text}")
        assert "Image 3 of 10" in counter_el.text, f"Expected Image 3 of 10, got {counter_el.text}"
        
        # Step 4: Refresh page and verify persistence
        print("Testing page refresh persistence...")
        driver.refresh()
        time.sleep(2)
        counter_el = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Image ') and contains(., ' of 10')]")))
        print(f"After browser refresh, counter text: {counter_el.text}")
        assert "Image 3 of 10" in counter_el.text, f"Expected Image 3 of 10 after refresh, got {counter_el.text}"
        
        # Step 5: Verify saved records
        records = glob.glob("artifacts/ml/defect_annotations/records/*.json")
        saved_pilot = {}
        for r in records:
            with open(r, "r") as fp:
                d = json.load(fp)
            if "pilot" in d.get("image_id", ""):
                saved_pilot[d.get("image_id")] = d
                
        print(f"Verified saved pilot records: {list(saved_pilot.keys())}")
        assert "pilot_001" in saved_pilot, "pilot_001 was not persisted!"
        assert saved_pilot["pilot_001"]["multi_label_defects"]["healthy"] is True, "pilot_001 healthy flag not true!"
        assert "pilot_002" in saved_pilot, "pilot_002 was not persisted!"
        assert saved_pilot["pilot_002"]["multi_label_defects"]["damage"] is True, "pilot_002 damage flag not true!"
        
        print("\n==========================================")
        print("VERIFICATION RESULT: PASS")
        print("Image 1 -> Image 2 -> Image 3 progression verified successfully!")
        print("Saved labels verified in persisted records!")
        print("Page refresh state persistence verified successfully!")
        print("==========================================\n")
        return True
    finally:
        driver.quit()
        cleanup_pilot_test_records()

if __name__ == "__main__":
    success = run_test()
    if not success:
        sys.exit(1)
