import requests
import json
import csv
from bs4 import BeautifulSoup
from pprint import pprint
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import logging
Mock=False
from retry_decorator import retry_with_backoff
from text_utils import clean_text

conferenceID='16147' # KubeCon India 2024
TrackID='5092' #Platform Engineering
personalID="aa...............dbae"     # get from browser or URL
#########################
url = 'https://sessionize.com/app/organizer/event/evaluation/sessions-stat/%s/%s'%(conferenceID,TrackID)
headers = {
    'Cookie': '_ga=GA1.1.158483382...; _ga_9RSMQ9D5LK=GS1.1.1724659160.20.1.1724662171.0.0.0',
    'Origin': 'https://sessionize.com',
    'Referer': 'https://sessionize.com/app/organizer/event/evaluation/stats/%s/%s/%s'%(conferenceID,TrackID,personalID),
    'Request-Id': '|78...............f1',
}
##################
class Speaker:
    def __init__(self, name, title=None, company=None, description=None):
        self.name = name
        self.title = title
        self.company = company
        self.description = description

    def to_dict(self, index):
        """Convert speaker to a dictionary with indexed keys"""
        return {
            f'speaker{index}_name': self.name,
            f'speaker{index}_title': self.title,
            f'speaker{index}_company': self.company,
            f'speaker{index}_bio': self.description
        }

    def __repr__(self):
        return f"Speaker(name='{self.name}', Company='{self.company}')"

####################
class Session:
    def __init__(self, session_id, rank, points, title, desc=None, oss_proj=None, benefit=None, cncf_proj=None, add_res=None, sec_format=None, speakers=None):
        self.session_id = session_id
        self.rank = rank
        self.points = points
        self.oss_proj = oss_proj
        self.cncf_proj = cncf_proj
        self.title = title
        self.desc = desc
        self.benefit = benefit
        self.add_res = add_res
        self.sec_format = sec_format
        self.speakers = speakers if speakers is not None else []

    def to_dict(self):
        """Convert session to a dictionary with organized fields"""
        # Base session info
        session_info = {
            'session_id': self.session_id,
            'rank': self.rank,
            'points': self.points,
            'title': self.title,
            'description': self.desc,
            'session_format': self.sec_format
        }
        
        # Project related info
        project_info = {
            'open_source_projects': self.oss_proj,
            'cncf_projects': self.cncf_proj,
            'ecosystem_benefits': self.benefit,
            'additional_resources': self.add_res
        }
        
        # Combine all information
        result = {**session_info, **project_info}
        
        # Add speaker information
        for i, speaker in enumerate(self.speakers, 1):
            speaker_dict = speaker.to_dict(i)
            result.update(speaker_dict)
        
        return result

    def add_speaker(self, speaker):
        self.speakers.append(speaker)

    def __repr__(self):
        return (f"Session(session_id={self.session_id}, rank={self.rank}, points={self.points}, "
                f"title='{self.title}', desc='{self.desc}', benefit='{self.benefit}', open source projects='{self.oss_proj}' , addtional resource='{self.add_res}'"
                f"CNCF projects='{self.cncf_proj}', session_format='{self.sec_format}' speakers={self.speakers})")


@retry_with_backoff(max_retries=5, base_delay=1, max_delay=32)
def make_request(url, headers=None):
    """
    Send HTTP request with retry mechanism
    """
    return requests.get(url, headers=headers, verify=True, timeout=30)
##########################3
async def fetch_session_detail(session_id, headers, semaphore, session):
    """Asynchronously fetch session details"""
    async with semaphore:  # Limit concurrent requests
        session_url = f"https://sessionize.com/app/organizer/event/evaluation/rate/{conferenceID}/{TrackID}?sessionId={session_id}"
        try:
            async with session.get(session_url, headers=headers) as response:
                if response.status != 200:
                    logging.error(f"Failed to fetch session detail: {session_url}, status code: {response.status}")
                    return None
                return await response.text()
        except Exception as e:
            logging.error(f"Error fetching session detail: {session_url}, error: {str(e)}")
            return None

def parse_session_detail(html_content, session):
    """Parse session detail HTML content"""
    if not html_content:
        return None
        
    soup = BeautifulSoup(html_content, 'html.parser')
    # title
    title_elem = soup.select_one('div.ibox-title h3')
    if title_elem:
        session.title = clean_text(title_elem.text.strip())
    
    # description
    desc_elem = soup.find('div', class_='evaluation-session')
    if desc_elem:
        desc_p = desc_elem.find('p', class_='es-description')
        if desc_p:
            session.desc = clean_text(desc_p.text.strip())

    # find all th table element
    th_elements = soup.find_all('th')
    for th in th_elements:
        small = th.find('small')
        if small:
            if small.text.strip() == 'Open source projects':
                session.oss_proj = clean_text(th.find_next_sibling('td').text.strip())
            elif small.text.strip() == 'CNCF-hosted software':
                session.cncf_proj = clean_text(th.find_next_sibling('td').text.strip())
            elif small.text.strip() == 'Benefits to the ecosystem':
                session.benefit = clean_text(th.find_next_sibling('td').text.strip())
            elif small.text.strip() == 'Session format':
                session.sec_format = clean_text(th.find_next_sibling('td').text.strip())
            elif small.text.strip() == 'Additional resources':
                session.add_res = clean_text(th.find_next_sibling('td').text.strip())

    # Process speakers
    #speaker_divs = soup.find_all('div', class_='speaker-item')
    speaker_divs = soup.find_all('div', class_='social-body') # seems the div nclass changed.

    for speaker_div in speaker_divs:
        speaker_info = {
            'name': clean_text(speaker_div.find('h4').text.strip()),
            'title': None,
            'company': None,
            'description': None
        }
        
        # Find all th elements within this speaker div
        for th in speaker_div.find_all('th'):
            if th and th.text.strip() == "Company":
                speaker_info['company'] = clean_text(th.find_next_sibling('td').text.strip())
            elif th and th.text.strip() == "Speaker Title":
                speaker_info['title'] = clean_text(th.find_next_sibling('td').text.strip())
        
        desc_p = speaker_div.find('p', class_='force-wrap')
        if desc_p:
            speaker_info['description'] = clean_text(desc_p.text.strip())
        
        session.add_speaker(Speaker(
            name=speaker_info['name'],
            title=speaker_info['title'],
            company=speaker_info['company'],
            description=speaker_info['description']
        ))
    
    return session

async def main():
    # write to excel
    with open('data.csv', 'w', newline='', encoding='utf-8') as outfile:
        # Organize fields by category
        session_fields = ['session_id', 'rank', 'points', 'title', 'description', 'session_format']
        project_fields = ['open_source_projects', 'cncf_projects', 'ecosystem_benefits', 'additional_resources']
        speaker_fields = []
        
        # Dynamically generate speaker fields for up to 8 speakers
        for i in range(1, 9):
            speaker_fields.extend([
                f'speaker{i}_name',
                f'speaker{i}_title',
                f'speaker{i}_company',
                f'speaker{i}_bio'
            ])
        
        fieldnames = session_fields + project_fields + speaker_fields
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        nextPage = True
        page = 1
        sessions = []
        
        # Fetch all session list
        while nextPage:
            if Mock:
                with open('mock_list.json', 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    nextPage = False
            else:
                data = {
                    'view': 'Top',
                    'q': '',
                    'page': page,
                    'userId': personalID
                }
                response = requests.post(url, headers=headers, data=data)
                print(f"Fetching session list for page {page}")
                if response.status_code != 200:
                    print(f"Error: Failed to get session list for page {page}, status code: {response.status_code}")
                    break
                json_data = response.json()
                nextPage = json_data.get('nextPage')
                page += 1
            
            for session in json_data.get('sessions', []):
                session_obj = Session(
                    session_id=session.get('sessionId'),
                    rank=session.get('rank_'),
                    points=session.get('points_'),
                    title=session.get('title')
                )
                if not any(s.session_id == session_obj.session_id for s in sessions):
                    sessions.append(session_obj)

        if Mock:
            # Handle Mock mode
            with open('mock_session.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
                sessions = [sessions[0]]
                parse_session_detail(html_content, sessions[0])
                writer.writerow(sessions[0].to_dict())
        else:
            # Use async concurrent requests to fetch session details
            semaphore = asyncio.Semaphore(10)  # Limit concurrent requests to 10
            async with aiohttp.ClientSession() as session:
                # Create all tasks
                tasks = []
                for session_obj in sessions:
                    task = fetch_session_detail(session_obj.session_id, headers, semaphore, session)
                    tasks.append((session_obj, task))
                
                # Use tqdm to show progress
                with tqdm(total=len(tasks), desc="Fetching session details") as pbar:
                    for session_obj, task in tasks:
                        html_content = await task
                        if html_content:
                            parse_session_detail(html_content, session_obj)
                            writer.writerow(session_obj.to_dict())
                        pbar.update(1)

if __name__ == "__main__":
    asyncio.run(main())
