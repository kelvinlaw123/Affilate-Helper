import subprocess

def run_proxy_checker():
    # Define the command and arguments
    command = [
        "python",  # Make sure 'python3' is correctly installed or use the full path to python
        "C:/Python312/Lib/site-packages/proxyz/proxyChecker.py",  # Update this path if needed
        "-p", "http",
        "-t", "20",
        "-s", "https://google.com",
        "-l", "proxyz_remaining_15.txt"
    ]

    try:
        # Run the command as a subprocess
        result = subprocess.run(command, check=True, capture_output=True, text=True)

        # Output result to console
        print("Output:")
        print(result.stdout)
        print("Error (if any):")
        print(result.stderr)

    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        print("Output:", e.output)
        print("Error:", e.stderr)

if __name__ == "__main__":
    run_proxy_checker()
