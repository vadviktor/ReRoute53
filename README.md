# reroute53-py

## Setup

```powershell
uv sync `
& .\.venv\Scripts\Activate.ps1
```

## Deploy

```powershell
op inject -f -i .env.tpl -o .env
$env:AWS_PROFILE = "ikon"
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 182497249286.dkr.ecr.eu-west-1.amazonaws.com
docker build --platform linux/amd64,linux/arm64/v8 -t reroute53:latest .
docker tag reroute53:latest 182497249286.dkr.ecr.eu-west-1.amazonaws.com/reroute53:latest
docker push 182497249286.dkr.ecr.eu-west-1.amazonaws.com/reroute53:latest
```

## Test. Apply to crontab.

```powershell
$env:AWS_PROFILE = "ikon"
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 182497249286.dkr.ecr.eu-west-1.amazonaws.com
docker run --rm 182497249286.dkr.ecr.eu-west-1.amazonaws.com/reroute53:latest
```
