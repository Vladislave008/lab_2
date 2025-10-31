from src.shell import Shell

def main() -> None:
    shell = Shell()
    while True:
        line = str(input('> '))
        if line.lower() in ['q']:
            break
        shell.parse_line(line)

if __name__ == "__main__":
    main()
