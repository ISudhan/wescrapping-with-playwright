import schedule
import time
import subprocess

def run_blinkit():
    print("Running Blinkit scraper...")
    subprocess.run(["python", "blinkit.py"])

def run_swiggy():
    print("Running Swiggy scraper...")
    subprocess.run(["python", "swiggy.py"])

def run_zepto():
    print("Running Zepto scraper...")
    subprocess.run(["python", "zepto.py"])

schedule.every().day.at("06:32").do(run_blinkit)
schedule.every().day.at("08:30").do(run_swiggy)
schedule.every().day.at("09:00").do(run_zepto)

while True:
    schedule.run_pending()
    time.sleep(1)  
    
