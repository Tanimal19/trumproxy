from mitmproxy import http
import geoip2.database
import geoip2.errors

# 替換為你下載的 GeoLite2 資料庫路徑
GEOIP_DB_PATH = "./GeoLite2-Country.mmdb"
geoip_reader = geoip2.database.Reader(GEOIP_DB_PATH)


def request(flow: http.HTTPFlow):
    ip = flow.server_conn.peername[0]
    try:
        response = geoip_reader.country(ip)
        country = response.country.name
        country_code = response.country.iso_code
        print(f"來自 {ip} ({country} {country_code}）的請求已被記錄。")
    except geoip2.errors.AddressNotFoundError:
        print(f"IP {ip} 無法辨識國家。")
    except Exception as e:
        print(f"處理 IP {ip} 發生錯誤: {e}")
