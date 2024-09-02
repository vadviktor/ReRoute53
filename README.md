# route53-ddns-updater-py

## Setup

```powershell
python -m venv .venv `
& .\.venv\Scripts\Activate.ps1 `
python -m pip install -U -r requirements.dev.txt
```

## Deploy

```powershell
op inject -i .env.tpl -o .env
docker -H "ssh://rpi5-8" build -t "rpi5-8:5000/route53-ddns-updater-py:latest" .
docker -H "ssh://rpi5-8" push "rpi5-8:5000/route53-ddns-updater-py"
docker run --rm "route53-ddns-updater-py:latest"
```

## Test. Apply to crontab.

```powershell
docker -H "ssh://rpi5-8" run --rm rpi5-8:5000/"route53-ddns-updater-py
```
