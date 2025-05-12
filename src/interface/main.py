import subprocess

def main() -> None:
    print("Hello from hello-world!")
    subprocess.run(["cowsay", "Hello from hello-world!"], check=True)
    
if __name__ == "__main__":
    main()