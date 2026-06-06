"""Check domain registration status."""
import json, urllib.request

url = "https://rdap.verisign.com/com/v1/domain/bzmli.com"
req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
        if 'ldhName' in data:
            print('✅ Domain IS registered')
            print(f"   Domain: {data.get('ldhName')}")
        if 'events' in data:
            for e in data['events']:
                print(f"   {e['eventAction']}: {e['eventDate']}")
        if 'nameservers' in data and data['nameservers']:
            print('   NameServers:')
            for ns in data['nameservers']:
                print(f"     - {ns.get('ldhName', 'N/A')}")
        else:
            print('   ⚠️  No nameservers set yet')
except urllib.error.HTTPError as e:
    if e.code == 404:
        print('❌ Domain NOT found in registry - registration still pending')
    else:
        print(f'❌ Error {e.code}: {e.reason}')
except Exception as e:
    print(f'❌ Error: {e}')
