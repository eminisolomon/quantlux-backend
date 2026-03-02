import os
import glob


def main():
    search_str = "app.schemas"
    replace_str = "app.schemas"

    python_files = glob.glob("**/*.py", recursive=True)

    count = 0
    for file in python_files:
        with open(file, "r") as f:
            content = f.read()

        if search_str in content:
            new_content = content.replace(search_str, replace_str)
            with open(file, "w") as f:
                f.write(new_content)
            count += 1
            print(f"Updated {file}")

    print(f"Total files updated: {count}")


if __name__ == "__main__":
    main()
