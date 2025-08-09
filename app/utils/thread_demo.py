import threading
import time
import os
import psutil

def worker_thread(name, duration):
    """A function that will run in a separate thread"""
    print(f"Thread {name} started - Thread ID: {threading.current_thread().ident}")
    print(f"  Running on Process ID: {os.getpid()}")
    
    # Simulate work
    for i in range(duration):
        time.sleep(1)
        print(f"  Thread {name}: Working... {i+1}/{duration}")
    
    print(f"Thread {name} completed")

def show_process_info():
    """Show current process and thread information"""
    process = psutil.Process(os.getpid())
    
    print("\n=== PROCESS INFORMATION ===")
    print(f"Process ID (PID): {process.pid}")
    print(f"Process Name: {process.name()}")
    print(f"Memory Usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
    print(f"Number of Threads: {process.num_threads()}")
    print(f"CPU Cores Available: {psutil.cpu_count()}")
    
    # Show all threads
    print("\n=== THREADS IN THIS PROCESS ===")
    for thread in threading.enumerate():
        print(f"  - {thread.name} (ID: {thread.ident}, Alive: {thread.is_alive()})")

def main():
    print("=== THREAD DEMONSTRATION ===\n")
    
    # Show initial state
    show_process_info()
    
    print("\n=== CREATING THREADS ===")
    # Create multiple threads
    threads = []
    for i in range(3):
        t = threading.Thread(target=worker_thread, args=(f"Worker-{i+1}", 3))
        threads.append(t)
        t.start()
        print(f"Started thread: {t.name}")
    
    # Show state with multiple threads
    time.sleep(0.5)  # Let threads start
    show_process_info()
    
    # Wait for all threads to complete
    print("\n=== WAITING FOR THREADS TO COMPLETE ===")
    for t in threads:
        t.join()
    
    print("\n=== ALL THREADS COMPLETED ===")
    show_process_info()

if __name__ == "__main__":
    main()