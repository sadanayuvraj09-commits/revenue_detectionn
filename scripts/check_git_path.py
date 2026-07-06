import os
import subprocess


def main():
    path_value = os.environ.get("PATH", "")
    print("SYSTEM PATH:")
    print(path_value)
    print()

    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        print("Git is installed:", result.stdout.strip())
    except FileNotFoundError:
        print("Git was not found on this system.")
        print(
            'Please add "C:\\Program Files\\Git\\bin" and "C:\\Program Files\\Git\\cmd" to your PATH.'
        )
    except subprocess.CalledProcessError as error:
        print("Git command failed:", error)


if __name__ == "__main__":
    main()
