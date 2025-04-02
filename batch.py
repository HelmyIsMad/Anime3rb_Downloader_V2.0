import os
def main():
    links: list[str] = []
    while True:
        link = input("Enter the url of the anime (e.g. https://anime3rb.com/titles/naruto) or press enter to start downloading: ")
        if link.replace(" ", "").strip() == "":
            break
        links.append(link)
    
    for link in links:
        os.system(f"start cmd /k \"cd /d {os.path.dirname(os.path.realpath(__file__))} & python main.py {link.strip()} & exit\"")

if __name__ == "__main__":
    main()