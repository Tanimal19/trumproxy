# Trumproxy

impose tariff on network traffic  
using [mitmproxy](https://mitmproxy.org/) and [wireguard](https://www.wireguard.com/)  

**This is a final project of NTU CNL 2025**  

## For server

```bash
docker-compose up --build -d    # build image and run container in background
docker stop trumproxy           # to stop container
docker start trumproxy          # to start container again
```

## For client

make sure your client and the server is connnected to the same LAN (wifi).

install wireguard and set the config as

```
[Interface]
PrivateKey = LibIxv8PBnEb2jv2MsGbjCxkD6DFEyiPA5bwM4Svgl4=
Address = 10.0.0.1/32
DNS = 10.0.0.53

[Peer]
PublicKey = HEa+HI/Sb5MYPxEawU/VEvB3715+dmE2qgeHwu7TmlE=
AllowedIPs = 0.0.0.0/0
Endpoint = {change to your server ip}:51820
```

after connecting, go to mitm.it and follow the steps

## Troubleshooting

### How to see my server ip?

If running on windows, go to Powershell and type `ipconfig`, your server ip is the IPv4 address under the "Wifi" section.

## For Developer

for python functions to control trumproxy, please refer to `trumproxy.py`
