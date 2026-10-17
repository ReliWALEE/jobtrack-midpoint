"""Add fictional demo records through the running API. Safe to repeat."""
import json
from urllib.request import Request,urlopen
BASE='http://127.0.0.1:8000/api/applications'
with urlopen(BASE) as r: existing={(x['company'],x['title']) for x in json.load(r)}
rows=[('Fable Studio','Frontend Developer','Remote',95000,'Full-time','Interview'),('Arc Systems','Backend Engineer','Chicago, IL',110000,'Full-time','Applied'),('Evergreen Health','Data Analyst','Austin, TX',78000,'Contract','Saved'),('Cedar Finance','Product Designer','New York, NY',125000,'Full-time','Offer'),('Brightside','Engineering Intern','Remote',60000,'Internship','Rejected')]
for company,title,location,salary,employment_type,status in rows:
 if (company,title) in existing:continue
 data=dict(company=company,title=title,location=location,salary=salary,employment_type=employment_type,status=status,applied_date='2026-10-16',notes='Fictional demo application')
 with urlopen(Request(BASE,data=json.dumps(data).encode(),headers={'Content-Type':'application/json'})) as r: print('Added',json.load(r)['company'])
