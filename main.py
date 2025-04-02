import os
import time
import threading
import sys
from collections import deque
import cloudscraper
from bs4 import BeautifulSoup

queue = deque()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

scraper = cloudscraper.create_scraper()

def download_video(url, filename):
    response = scraper.get(url, headers=headers, stream=True)

    if response.status_code != 200:
        print(f"Failed to download video: {response.status_code}")
        return

    total_size = int(response.headers.get('content-length', 0))
    os.makedirs("output", exist_ok=True)

    with open(f"output/{filename}", 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            f.write(chunk)
            print(f"Downloading... {f.tell() / total_size * 100:.2f}%" + 50 * ' ', end='\r')

def start_downloads(anime_name: str, episodes: int):
    while not queue:
        time.sleep(1)

    for counter in range(start, end + 1):
        link = queue.popleft()
        print(f"Starting download for episode {counter}/{episodes}...", end='\r')

        ep_name = f"{anime_name} - Episode {counter}"
        if counter == episodes:
            ep_name += " [END]"
        ep_name += '.mp4'

        download_video(link, ep_name)
        print(f"Episode {counter}/{episodes} downloaded successfully!")

def get_episode_cnt(soup: BeautifulSoup) -> int:
    try:
        cnt = soup.find_all('p', class_="text-lg leading-relaxed")[1].text.strip()
        return int(cnt)
    except (IndexError, ValueError, AttributeError):
        print("Failed to retrieve episode count.")
        sys.exit(1)

def get_episode_links(url: str, episodes: int) -> list[str]:
    res = []
    i = url.index("titles")
    base_url = url[:i] + "episode" + url[i + 6:]

    for episode in range(1, episodes + 1):
        res.append(f"{base_url}/{episode}")
    return res

def get_download_links(episode_links: list[str]):
    global queue, start

    for episode in episode_links[start - 1:]:
        page = scraper.get(episode, headers=headers)
        soup = BeautifulSoup(page.content, "html.parser")

        download_links_holder = soup.find("div", class_="flex-grow flex flex-wrap gap-4 justify-center")
        if not download_links_holder:
            print(f"Failed to find download links for {episode}")
            continue

        download_links = download_links_holder.find_all("label")
        desired = [None, None]

        for link in download_links:
            if "480" in link.text:
                desired = [480, link]
            elif "720" in link.text and desired[0] != 1080:
                desired = [720, link]
            elif not desired[1]:  
                desired = [1080, link]  

        if desired[1]:
            queue.append(desired[1].parent.find("a")["href"])
        else:
            print(f"No valid download link found for {episode}")

def main(url):
    MY_NAME = """
██   ██ ███████ ██      ███    ███ ██    ██ 
██   ██ ██      ██      ████  ████  ██  ██  
███████ █████   ██      ██ ████ ██   ████   
██   ██ ██      ██      ██  ██  ██    ██    
██   ██ ███████ ███████ ██      ██    ██    
"""
    print(MY_NAME)
    print("Welcome to Anime3rb Downloader")

    page = scraper.get(url, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")

    anime_name = url[url.index("titles") + 7:]
    episodes_cnt = get_episode_cnt(soup)

    episode_links = get_episode_links(url, episodes_cnt)
    print(f"{anime_name} has {episodes_cnt} episodes.")

    global start, end
    # start = 1
    start = int(input("Enter the episode number to start from: "))
    while start < 1 or start > episodes_cnt:
        start = int(input(f"Invalid episode number. Please enter a number between 1 and {episodes_cnt} (inclusive): "))
    
    # end = episodes_cnt
    end = int(input("Enter the episode number to end at: "))
    while end < 1 or end > episodes_cnt or end < start:
        end = int(input(f"Invalid episode number. Please enter a number between {start} and {episodes_cnt} (inclusive): "))
    

    threading.Thread(target=get_download_links, args=[episode_links]).start()
    start_downloads(anime_name, episodes_cnt)

    print("Thanks for using Anime3rb Downloader :)")
    os.system("pause > nul")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        main(input("Enter the URL of the anime (e.g. https://anime3rb.com/titles/naruto): ").strip())
    else:
        main(sys.argv[1])
