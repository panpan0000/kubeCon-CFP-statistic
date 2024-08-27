This is an automatic parser for KubeCon CFP reviewers.

NOTE: You should make the changes BEFORE run this scripts.

Usage:

0. go to your sessionize CFP Evaluation Page --> CFS Page
1. On your Brower, click "Inspect" --> "Network" --> "Fetch/XHR" --> Find an Rest Call --> Copy --> Copy as cURL
2. retrieve the contents out of the cURL
	a. from the URL, you can get conferenceID & TrackID:  example `https://sessionize.com/app/organizer/event/evaluation/tabboxes/16147/5092`, `16147` stands for KubeCon India 2024, `5092` stands for Platform Engineering track.
	b. get `Cookie` and `Request-Id` from Headers
	c. get `userId`(I called it personalID) in the --data-raw part

3. fill those data into the python code
4. pip3 install -r requirements.txt
5. run the script `python3 generate-report.py`
6. get result in `data.csv`









