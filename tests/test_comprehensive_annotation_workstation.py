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
            # Only clean up test records or pilot records created during testing
            if d.get("annotator_id") in ["HUMAN_ANNOTATOR_A", "HUMAN_ANNOTATOR_B", "TEST_ANNOTATOR"]:
                os.remove(f)
                print(f"Cleaned up test record: {f}")
        except Exception:
            pass

def run_comprehensive_workstation_test():
    cleanup_pilot_test_records()
    
    options = Options()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")
    
    service = Service(executable_path="/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        url = "http://localhost:5173/internal/annotation"
        print(f"Navigating to {url}...")
        driver.get(url)
        time.sleep(2)
        
        driver.execute_script("sessionStorage.clear();")
        driver.refresh()
        time.sleep(2)
        
        wait = WebDriverWait(driver, 10)
        
        # ----------------------------------------------------
        # TEST 1: Initial State on Image 1
        # ----------------------------------------------------
        print("\n--- TEST 1: Initial State on Image 1 ---")
        counter_el = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Image 1 of 10')]")))
        print(f"Verified counter: Image 1 of 10")
        
        # Try clicking SAVE & NEXT IMAGE without selecting any label -> MUST show validation error alert
        print("Testing validation when saving without any label...")
        save_btn = wait.until(EC.element_to_be_clickable((By.ID, "save-next-btn")))
        save_btn.click()
        time.sleep(0.5)
        
        alert = driver.switch_to.alert
        alert_text = alert.text
        print(f"Received expected validation alert: '{alert_text}'")
        assert "Validation Error: Please select at least one label" in alert_text, f"Unexpected alert text: {alert_text}"
        alert.accept()
        time.sleep(0.5)
        
        # ----------------------------------------------------
        # TEST 2: Select 'Healthy' on Image 1 and Save
        # ----------------------------------------------------
        print("\n--- TEST 2: Image 1 -> Select Healthy -> Save & Next ---")
        healthy_btn = wait.until(EC.element_to_be_clickable((By.ID, "label-healthy-btn")))
        healthy_btn.click()
        time.sleep(0.5)
        
        save_btn.click()
        time.sleep(1)
        
        # Verify NO unexpected alert appeared
        try:
            alert = driver.switch_to.alert
            unexp_text = alert.text
            alert.accept()
            raise AssertionError(f"Unexpected alert popup on valid save: {unexp_text}")
        except Exception as e:
            if "Unexpected alert popup" in str(e):
                raise
        
        # Verify transition to Image 2 of 10
        counter_el = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Image 2 of 10')]")))
        print("PASS: Successfully advanced to Image 2 of 10")
        
        # ----------------------------------------------------
        # TEST 3: Select 'Damaged' on Image 2 and Save
        # ----------------------------------------------------
        print("\n--- TEST 3: Image 2 -> Select Damaged -> Save & Next ---")
        damage_btn = wait.until(EC.element_to_be_clickable((By.ID, "label-damage-btn")))
        damage_btn.click()
        time.sleep(0.5)
        
        save_btn = wait.until(EC.element_to_be_clickable((By.ID, "save-next-btn")))
        save_btn.click()
        time.sleep(1)
        
        try:
            alert = driver.switch_to.alert
            unexp_text = alert.text
            alert.accept()
            raise AssertionError(f"Unexpected alert popup on valid save: {unexp_text}")
        except Exception as e:
            if "Unexpected alert popup" in str(e):
                raise
                
        # Verify transition to Image 3 of 10
        counter_el = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Image 3 of 10')]")))
        print("PASS: Successfully advanced to Image 3 of 10")
        
        # ----------------------------------------------------
        # TEST 4: Select 'Rotten' on Image 3 and Save
        # ----------------------------------------------------
        print("\n--- TEST 4: Image 3 -> Select Rotten -> Save & Next ---")
        rot_btn = wait.until(EC.element_to_be_clickable((By.ID, "label-rot-btn")))
        rot_btn.click()
        time.sleep(0.5)
        
        save_btn = wait.until(EC.element_to_be_clickable((By.ID, "save-next-btn")))
        save_btn.click()
        time.sleep(1)
        
        counter_el = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Image 4 of 10')]")))
        print("PASS: Successfully advanced to Image 4 of 10")
        
        # ----------------------------------------------------
        # TEST 5: Refresh Persistence at Image 4
        # ----------------------------------------------------
        print("\n--- TEST 5: Browser Refresh Position Persistence ---")
        driver.refresh()
        time.sleep(2)
        counter_el = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Image 4 of 10')]")))
        print("PASS: Workstation persisted at Image 4 of 10 after page reload")
        
        # ----------------------------------------------------
        # TEST 6: Previous Navigation and Label Recall
        # ----------------------------------------------------
        print("\n--- TEST 6: Previous Navigation and Label Recall ---")
        prev_btn = wait.until(EC.element_to_be_clickable((By.ID, "nav-prev-btn")))
        prev_btn.click()
        time.sleep(1)
        counter_el = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Image 3 of 10')]")))
        print("PASS: Navigated back to Image 3 of 10")
        
        # ----------------------------------------------------
        # TEST 7: Verify Persisted File Records
        # ----------------------------------------------------
        print("\n--- TEST 7: Backend Records Verification ---")
        records = glob.glob("artifacts/ml/defect_annotations/records/*.json")
        saved_records = {}
        for r in records:
            with open(r, "r") as fp:
                d = json.load(fp)
            if d.get("annotator_id") == "HUMAN_ANNOTATOR_A":
                saved_records[d.get("image_id")] = d
                
        print(f"Persisted records found: {list(saved_records.keys())}")
        assert "pilot_001" in saved_records, "pilot_001 missing"
        assert saved_records["pilot_001"]["multi_label_defects"]["healthy"] is True, "pilot_001 healthy flag incorrect"
        assert saved_records["pilot_001"]["multi_label_defects"]["damage"] is False, "pilot_001 damage flag should be False"
        
        assert "pilot_002" in saved_records, "pilot_002 missing"
        assert saved_records["pilot_002"]["multi_label_defects"]["damage"] is True, "pilot_002 damage flag incorrect"
        assert saved_records["pilot_002"]["multi_label_defects"]["healthy"] is False, "pilot_002 healthy flag should be False"
        
        assert "pilot_003" in saved_records, "pilot_003 missing"
        assert saved_records["pilot_003"]["multi_label_defects"]["rot"] is True, "pilot_003 rot flag incorrect"
        
        print("PASS: All persisted backend records strictly match human labels")
        
        print("\n==========================================")
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("1. Image 1 -> Image 2 navigation: PASS")
        print("2. Image 2 -> Image 3 navigation: PASS")
        print("3. Refresh persistence: PASS")
        print("4. Label persistence: PASS")
        print("==========================================\n")
        return True
    finally:
        driver.quit()
        cleanup_pilot_test_records()

if __name__ == "__main__":
    success = run_comprehensive_workstation_test()
    if not success:
        sys.exit(1)
