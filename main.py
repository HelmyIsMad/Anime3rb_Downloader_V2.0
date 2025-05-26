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

def get_download_links(episode_links: list[str], quality_preference: str):
    global queue, start, end # Ensure 'end' is recognized as global if not already implicitly

    quality_order = ["1080", "720", "480"]
    
    # Loop through the specified range of episodes
    for current_loop_idx, episode_url in enumerate(episode_links[start - 1 : end]):
        actual_episode_number = start + current_loop_idx

        page = scraper.get(episode_url, headers=headers)
        soup = BeautifulSoup(page.content, "html.parser")

        download_links_holder = soup.find("div", class_="flex-grow flex flex-wrap gap-4 justify-center")
        if not download_links_holder:
            print(f"Failed to find download links section for episode {actual_episode_number} ({episode_url})")
            continue

        available_qualities = {}
        for label_tag in download_links_holder.find_all("label"):
            text_content = label_tag.text.strip().lower()
            link_tag = label_tag.parent.find("a")
            if link_tag and link_tag.has_attr("href"):
                # Extract quality string like "1080", "720", "480"
                if "1080" in text_content:
                    available_qualities["1080"] = link_tag["href"]
                elif "720" in text_content:
                    available_qualities["720"] = link_tag["href"]
                elif "480" in text_content:
                    available_qualities["480"] = link_tag["href"]
        
        if not available_qualities:
            print(f"No download links found for episode {actual_episode_number} ({episode_url})")
            continue

        chosen_url = None
        
        # 1. Try preferred quality
        if quality_preference in available_qualities:
            chosen_url = available_qualities[quality_preference]
        else:
            # 2. Try fallback qualities (lower or equal to preference)
            try:
                # Find where the preferred quality sits in our defined order
                preferred_quality_index = quality_order.index(quality_preference)
            except ValueError:
                # This case should ideally be prevented by input validation in main()
                # but as a safeguard, treat as if highest preference was given.
                print(f"Warning: Invalid quality preference '{quality_preference}' received. Assuming highest quality preference for fallback.")
                preferred_quality_index = 0 # Default to try 1080p first in fallback

            # Iterate from the preferred quality downwards
            for quality_to_try in quality_order[preferred_quality_index:]:
                if quality_to_try in available_qualities:
                    chosen_url = available_qualities[quality_to_try]
                    # Print message only if a fallback was chosen (i.e. quality_to_try is different from quality_preference)
                    if quality_to_try != quality_preference:
                        print(f"Quality {quality_preference}p not found for episode {actual_episode_number}, downloading {quality_to_try}p instead.")
                    break 
        
        if chosen_url:
            queue.append(chosen_url)
        else:
            # 3. If no suitable link found (neither preferred nor any valid fallback)
            print(f"Could not find suitable download link for episode {actual_episode_number} (tried {quality_preference}p and lower).")

def main(url):
    MY_NAME = """
██   ██ ███████ ██      ███    ███ ██    ██ 
    # end = episodes_cnt
    end = int(input("Enter the episode number to end at: "))
    while end < 1 or end > episodes_cnt or end < start:
        end = int(input(f"Invalid episode number. Please enter a number between {start} and {episodes_cnt} (inclusive): "))
    
    valid_numeric_qualities = ["1080", "720", "480"]
    quality_preference = None
    while True:
        user_input = input("Enter preferred quality (1080, 720, 480): ").strip().lower()
        normalized_quality = user_input.replace("p", "")
        if normalized_quality in valid_numeric_qualities:
            quality_preference = normalized_quality
            break
        else:
            print("Invalid quality. Please enter 1080, 720, or 480 (e.g., 720p or 720).")

    # Ensure quality_preference is passed to the thread
    threading.Thread(target=get_download_links, args=[episode_links, quality_preference]).start()
    start_downloads(anime_name, episodes_cnt)

    print("Thanks for using Anime3rb Downloader :)")
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
