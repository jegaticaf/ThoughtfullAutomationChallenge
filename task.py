from config import OUTPUT_FOLDER
from libraries.common import log_message, print_version, create_or_clean_dir, capture_page_screenshot
from libraries.process import Process

def main():
    """
    Main function that calls all other functions
    """
    create_or_clean_dir(OUTPUT_FOLDER)
    process = Process({})
    try:
        process.start()
    except Exception as e:
        capture_page_screenshot(OUTPUT_FOLDER)
        log_message("An unexpected error was encountered during the process: {}".format(str(e)))
        raise e
    finally:
        process.finish()

if __name__ == "__main__":
    digital_worker_name = "Automation Training Challenge 2 Project"
    log_message("Start - {}".format(digital_worker_name))
    print_version()
    main()
    log_message("End - {}".format(digital_worker_name))