# route53-ddns-updater-py

```shell
docker build -t "route53-ddns-updater-py:$(date +%Y-%m-%d)" .
docker -H "ssh://rpi@192.168.1.222" build -t "route53-ddns-updater-py:$(date +%Y-%m-%d)" .
docker run --rm "route53-ddns-updater-py:$(date +%Y-%m-%d)"
```

```powershell
docker build -t "route53-ddns-updater-py:$((Get-Date).ToString('yyyy-MM-dd'))" .
docker -H "ssh://rpi@192.168.1.222" build -t "route53-ddns-updater-py:$((Get-Date).ToString('yyyy-MM-dd'))" .
docker run --rm "route53-ddns-updater-py:$((Get-Date).ToString('yyyy-MM-dd'))"
```
