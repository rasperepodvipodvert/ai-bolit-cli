Install
---
```bash
mkdir /opt/ai
cd /opt/ai
git clone https://github.com/rasperepodvipodvert/ai-bolit-cli.git
pip3 install -r /opt/ai/requirements.txt
```

How to Use
---
Check sites on VPS/VDS/etc...
```bash
python3 /opt/ai/start.py scan #scan all sites
python3 /opt/ai/start.py # for help
```
Cron settings for auto update and scan
---

```
50 5 * * 0 python3 /opt/ai/start.py update
0 6 * * 0 python3 /opt/ai/start.py scan
0 9 * * 0 python3 /opt/ai/start.py send_report
```