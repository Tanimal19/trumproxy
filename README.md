# Trumproxy (CLI ver)

impose tariff on network traffic  
using [mitmproxy](https://mitmproxy.org/) and [wireguard](https://www.wireguard.com/)

## For server
```
docker-compose up --build -d               # build image and run container in background
docker-compose exec trumproxy /bin/bash    # exec into container

# in container
python main.py
```
then you should able to use the cli command
```
get tariff                           - get all tariff rules
get retain                           - get currently retained packets
set <country code> <tariff rate>     - set tariff
remove <country code>                - remove tariff
exit                                 - close the cli (you still need to ctrl-c to close the proxy)
```

## For client
install wireguard and set the config as
```
[Interface]
PrivateKey = LibIxv8PBnEb2jv2MsGbjCxkD6DFEyiPA5bwM4Svgl4=
Address = 10.0.0.1/32
DNS = 10.0.0.53

[Peer]
PublicKey = HEa+HI/Sb5MYPxEawU/VEvB3715+dmE2qgeHwu7TmlE=
AllowedIPs = 0.0.0.0/0
Endpoint = 192.168.1.103:51820
```

after connecting, go to mitm.it and follow the steps

## For Developer
for python functions to control trumproxy, please refer to `trumproxy.py`
