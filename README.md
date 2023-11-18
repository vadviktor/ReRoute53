# route53-ddns-updater-py

Update my Route53 DNS record as a DDNS.

```shell
AWS_ACCESS_KEY_ID="" \
AWS_SECRET_ACCESS_KEY="" \
AWS_HOSTED_ZONE_ID="" \
AWS_RECORD_NAME="" \
SENTRY_DSN="" \
python ./ddns/__main__.py
```

```powershell
$env:AWS_ACCESS_KEY_ID = ""
$env:AWS_SECRET_ACCESS_KEY = ""
$env:AWS_HOSTED_ZONE_ID = ""
$env:AWS_RECORD_NAME = ""
$env:SENTRY_DSN = ""
python .\ddns\__main__.py
```

```shell
rm -f ./ddns.pyz
rm -rf ./ddns
python -m pip install -r requirements.txt --target ddns
find . -name "*.dist-info" -type d -exec rm -rf {} \;
find . -name "__pycache__" -type d -exec rm -rf {} \;
touch ./ddns/__init__.py
cp ./__main__.py ./ddns/
python -m zipapp ./ddns -o ddns.pyz -p "/usr/bin/env python3" -c
```

Package up:

```powershell
Remove-Item -Path .\ddns.pyz
Remove-Item -Path .\ddns -Recurse -Force
python -m pip install -r requirements.txt --target ddns
Get-ChildItem -Path . -Filter *.dist-info -Recurse | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Filter __pycache__ -Recurse | Remove-Item -Recurse -Force
New-Item -ItemType "file" -Path .\ddns\ -Name __init__.py
Copy-Item -Path .\__main__.py -Destination .\ddns\
python -m zipapp .\ddns\ -o ddns.pyz -p "/usr/bin/env python3" -c
```
