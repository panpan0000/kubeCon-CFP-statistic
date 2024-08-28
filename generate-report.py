import requests
import json
import csv
from bs4 import BeautifulSoup
from pprint import pprint
Mock=False

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
    def __init__(self, name, title, company, desc):
        self.name = name
        self.title = title
        self.company = company
        self.desc = desc

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
        self.sec_format= sec_format
        self.speakers = speakers if speakers is not None else []

    def add_speaker(self, speaker):
        self.speakers.append(speaker)

    def to_dict(self):
        rep =   {'session_id': self.session_id, 
                'rank': self.rank ,
                'points': self.points ,
                'title': self.title ,
                'desc': self.desc ,
                'benefit': self.benefit ,
                'oss_proj': self.oss_proj ,
                'addition_res': self.add_res ,
                'cncf_proj': self.cncf_proj ,
                'session_format': self.sec_format,
                'speaker1': "",
                'speaker1-company': "",
                'speaker2': "",
                'speaker2-company': "",
                'speaker3': "",
                'speaker3-company': "",
                'speaker4': "",
                'speaker4-company': "",
                'speaker5': "",
                'speaker5-company': "",
                'speaker6': "",
                'speaker6-company': "",
                'speaker7': "",
                'speaker7-company': "",
                'speaker8': "",
                'speaker8-company': "",

                }
        for i,s in enumerate(self.speakers):
            rep["speaker"+str(i+1)]= s['name']
            rep["speaker"+str(i+1)+"-company"]=s.get('company')
        return rep;

    def __repr__(self):
        return (f"Session(session_id={self.session_id}, rank={self.rank}, points={self.points}, "
                f"title='{self.title}', desc='{self.desc}', benefit='{self.benefit}', open source projects='{self.oss_proj}' , addtional resource='{self.add_res}'"
                f"CNCF projects='{self.cncf_proj}', session_format='{self.sec_format}' speakers={self.speakers})")

##########################3
def main():

    # write to excel

    with open('data.csv', 'w', newline='') as outfile:
        fieldnames = [  'session_id', 'rank','points','title','desc',
                        'benefit','oss_proj','addition_res','cncf_proj',
                        'session_format',
                        'speaker1','speaker1-company',
                        'speaker2','speaker2-company',
                        'speaker3','speaker3-company',
                        'speaker4','speaker4-company',
                        'speaker5','speaker5-company',
                        'speaker6','speaker6-company',
                        'speaker7','speaker7-company',
                        'speaker8','speaker8-company',
                        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        nextPage=True
        page=1
        sessions=[]
        while nextPage :
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
                print("obtain the session list for page ", page)
                if response.status_code != 200:
                    print("Error , failed to get session list for page ", page, " response.status_code=", response.status_code)
                    exit(1)
                json_data = response.json()

                nextPage = json_data.get('nextPage') #there're next page avail
                page += 1
     
            for session in json_data.get('sessions', []):
                session_obj = Session(
                    session_id=session.get('sessionId'),
                    rank=session.get('rank_'),
                    points=session.get('points_'),
                    title=session.get('title'), 
                )
                existed=False
                for existing in sessions:
                    if session_obj.session_id == existing.session_id:
                        existed=True
                        break;
                if existed == False:
                    sessions.append(session_obj)

            for session in sessions:
                # construct the URL for each session
                session_url = f"https://sessionize.com/app/organizer/event/evaluation/rate/{conferenceID}/{TrackID}?sessionId={session.session_id}"
                print(f"Fetching HTML content from: {session_url}")

                if Mock:
                    with open('mock_session.html', 'r', encoding='utf-8') as f:
                        session_response = requests.Response()
                        session_response.status_code = 200
                        html_content = f.read()
                        sessions.clear()
                        sessions.append(session)
                else:
                    # get session detail
                    session_response = requests.get(session_url, headers=headers)
                    if session_response.status_code != 200:
                        print(f"Request session detail failed: {response.status_code}")
                    html_content = session_response.text


                soup = BeautifulSoup(html_content, 'html.parser')
                # title
                session.title=soup.select_one('div', class_='ibox').select_one('div.ibox-title h3').text.strip()
                # description
                session.desc = soup.find('div', class_='evaluation-session').find('p', class_='es-description').text.strip()

                # find all th table element
                th_elements = soup.find_all('th')

                for th in th_elements:
                    small = th.find('small') #all are ``small`
                    if small and small.text.strip() == 'Open source projects':
                        session.oss_proj = th.find_next_sibling('td').text.strip()
                    if small and small.text.strip() == 'CNCF-hosted software':
                        session.cncf_proj = th.find_next_sibling('td').text.strip()
                    if small and small.text.strip() == 'Benefits to the ecosystem':
                        session.benefit = th.find_next_sibling('td').text.strip()
                    if small and small.text.strip() == 'Session format':
                        session.sec_format = th.find_next_sibling('td').text.strip()
                    if small and small.text.strip() == 'Additional resources':
                        session.add_res = th.find_next_sibling('td').text.strip()
                for speaker_div in soup.find_all('div', class_='social-feed-box'):
                    speaker_info = {}
                    speaker_info['name'] = speaker_div.find('h4').strong.text.strip()
                    duplicated = False
                    for speaker in session.speakers:
                        if speaker['name'] == speaker_info['name']:
                            #duplicated, already existing.
                            duplicated = True
                            break
                    if duplicated:
                        continue
                    for th in speaker_div.find_all('th'):
                        if th and th.text.strip() == "Speaker Title":
                                speaker_info['title'] = th.find_next_sibling('td').text.strip()
                        if th and th.text.strip() == "Company":
                                speaker_info['company'] = th.find_next_sibling('td').text.strip()
                    speaker_info['description'] = speaker_div.find('p', class_='force-wrap').text.strip()
                    session.add_speaker(speaker_info)
                try:
                    writer.writerow(session.to_dict())
                    if Mock:
                        pprint(session.to_dict())
                except Exception as e:
                    print("Error happens in Session=",session)
                    print("Error=", e)
            
    #Print all sessions
    #pprint(sessions)

if __name__=="__main__":
        main()

