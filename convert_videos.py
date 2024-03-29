from os import walk
from os.path import join, isfile
from os import makedirs
import subprocess
import threading
import time

source_root = "/Users/harpapat/Downloads/videos_60fps"
destination_root = "/Users/harpapat/Downloads/videos_30fps"
files_to_process = set()
worker_threads = 4

def get_next(lock):
    lock.acquire()
    global files_to_process
    if len(files_to_process) == 0:
        file = None
    else:
        file = files_to_process.pop()
    lock.release()
    return file

def thread_task(lock):
    while(True):
        paths = get_next(lock)
        if paths is None:
            break
        (src_path, dst_path) = paths
        subprocess.run(["ffmpeg", "-y", "-i", src_path, "-r", "30", dst_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def observer_thread(max_elems, start_time):
    while len(files_to_process) > 0:
        processed_files = max_elems - len(files_to_process)
        time_elapsed_sec = time.time() - start_time
        if time_elapsed_sec > 0:
            processing_rate = processed_files * 60 / time_elapsed_sec
        print(f"\rprocessed: {len(files_to_process)}/{max_elems}", f"rate (file/min): {processing_rate}", end="")
        time.sleep(1)

def read_dir(dir_path):
    for (dirpath, dirnames, filenames) in walk(source_root):
        for filename in filenames:
            dst_path = dirpath.replace(source_root, destination_root)
            try:
                makedirs(dst_path)
            except FileExistsError:
                pass

    for (dirpath, dirnames, filenames) in walk(source_root):
        for filename in filenames:
            if ".mov" in filename.lower() or ".mp4" in filename.lower():
                src_path = join(dirpath, filename)
                dst_path = src_path.replace(source_root, destination_root)
                if ("._" not in filename):
                    global files_to_process
                    files_to_process.add((src_path, dst_path))
                    # command = f"ffmpeg -y -i \"{src_path}\" -r 30 \"{dst_path}\""
                    # print(command)
                    # subprocess.run(["ffmpeg", "-y", "-i", src_path, "-r", "30", dst_path])
                else:
                    pass
    
def main_task():
    read_dir(source_root)
    lock = threading.Lock()
    threads = []
    threads.append(threading.Thread(target=observer_thread, args=(len(files_to_process),time.time(),)))
    for i in range(worker_threads):
        threads.append(threading.Thread(target=thread_task, args=(lock,)))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

main_task()