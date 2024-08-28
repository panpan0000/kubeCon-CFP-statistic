# This is an automatic parser for KubeCon CFP reviewers.

Okay, I should have know that sessionize provides API ...


## NOTE: You should make below changes BEFORE running this scripts.

---

## Usage:




1. Go to your sessionize:  CFP Evaluation Page --> CFS Page

2. On your Browser, click "Inspect" --> "Network" --> "Fetch/XHR" --> Find an Rest Call --> Copy --> Copy as cURL

3. Retrieve the confident contents out of the cURL

   - from the URL, you can get conferenceID & TrackID:  example `https://sessionize.com/app/organizer/event/evaluation/tabboxes/16147/5092`, `16147` stands for KubeCon India 2024, `5092` stands for Platform Engineering track.

   - get `Cookie` and `Request-Id` from Headers

   - get `userId`(I called it personalID) in the `--data-raw` part

4. fill those data into the python code , to replace those variables

5. `pip3 install -r requirements.txt`

6. run the script `python3 generate-report.py`

7. get result in `data.csv`









