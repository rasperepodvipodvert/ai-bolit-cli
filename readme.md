Requirements
---
- Python3 (not testing on python2)

Install
---
```bash
apt install python3-pip -y
mkdir /opt/ai
cd /opt/ai
git clone https://github.com/rasperepodvipodvert/ai-bolit-cli.git
pip3 install -r /opt/ai/requirements.txt
```

How to Use
---
Check viruses on your sites (VPS/VDS/etc...)

```bash
# scan all sites
python3 /opt/ai/start.py scan

# update antivirus
python3 /opt/ai/start.py update

# send report to slack chat
python3 /opt/ai/start.py send_report

# command help 
python3 /opt/ai/start.py
```

Cron settings for auto update and scan
---
```bash
50 5 * * 0 python3 /opt/ai/start.py update
0 6 * * 0 python3 /opt/ai/start.py scan
0 9 * * 0 python3 /opt/ai/start.py send_report
```

