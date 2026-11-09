#!/usr/bin/env python3
"""Audit every shipped static archive member, API presence and upstream file hashes."""
import json, plistlib, struct, hashlib, re
from pathlib import Path

class verify:
    ARCHITECTURES = {0x100000C: "arm64", 0x1000007: "x86_64"}

    @staticmethod
    def version(value):
        return value >> 16, (value >> 8) & 255, value & 255

root = Path(__file__).resolve().parents[1]
def leaves(data,arch=None):
 if data[:4]==b'\xca\xfe\xba\xbe':
  count=struct.unpack_from('>I',data,4)[0]
  for i in range(count):
   cpu,sub,off,size,align=struct.unpack_from('>IIIII',data,8+20*i)
   yield from leaves(data[off:off+size],verify.ARCHITECTURES[cpu])
 elif data.startswith(b'!<arch>\n'):
  off=8
  while off<len(data):
   hdr=data[off:off+60]; assert hdr[58:60]==b'`\n';size=int(hdr[48:58]);name=hdr[:16].decode().strip();payload=data[off+60:off+60+size]
   if name.startswith('#1/'):
    n=int(name[3:]);name=payload[:n].rstrip(b'\0').decode();payload=payload[n:]
   if not name.startswith(('__.SYMDEF','/')):
    yield (arch,name,payload)
   off+=60+size+(size%2)
 else:raise ValueError('unexpected archive format')

def minimum(data):
 thin={b'\xcf\xfa\xed\xfe':('<',32),b'\xfe\xed\xfa\xcf':('>',32),b'\xce\xfa\xed\xfe':('<',28),b'\xfe\xed\xfa\xce':('>',28)}
 assert data[:4] in thin, 'non-MachO archive member '+repr(data[:16])
 endian,off=thin[data[:4]];cpu=struct.unpack_from(endian+'I',data,4)[0];n=struct.unpack_from(endian+'I',data,16)[0];floor=None;platform=None
 for _ in range(n):
  cmd,size=struct.unpack_from(endian+'II',data,off)
  if cmd==0x32:platform,packed=struct.unpack_from(endian+'II',data,off+8);floor=verify.version(packed)
  elif cmd in (0x24,0x25,0x2f,0x30):floor=verify.version(struct.unpack_from(endian+'I',data,off+8)[0]);platform={0x24:1,0x25:2,0x2f:3,0x30:4}[cmd]
  off+=size
 return verify.ARCHITECTURES[cpu],floor,platform

p=root/'Dovi.xcframework';rows=[];fail=[]
for lib in plistlib.loads((p/'Info.plist').read_bytes())['AvailableLibraries']:
 counts={}; symbols=set(); bound={'ios':(16,0,0),'tvos':(16,0,0),'macos':(14,0,0),'xros':(1,0,0)}[lib['SupportedPlatform']]
 b=(p/lib['LibraryIdentifier']/lib['LibraryPath']).read_bytes()
 for outer,name,data in leaves(b):
  arch,floor,platform=minimum(data)
  if floor is None or floor>bound:fail.append([lib['LibraryIdentifier'],name,str(floor)])
  if b'_dovi_rpu_set_polynomial_mapping' in data:symbols.add(arch)
  r=counts.setdefault(arch,{'objects':0,'floors':set(),'platforms':set()});r['objects']+=1;r['floors'].add(str(floor));r['platforms'].add(platform)
 for r in counts.values():r['floors']=sorted(r['floors']);r['platforms']=sorted(r['platforms'],key=str)
 assert set(counts)==set(lib['SupportedArchitectures'])
 assert symbols==set(counts),(lib,symbols)
 rows.append({'slice':lib['LibraryIdentifier'],'architectures':counts,'polynomial_mapping_symbols':sorted(symbols),'sha256':hashlib.sha256(b).hexdigest()})
records=re.findall(r"^([0-9a-f]{64})  (Dovi\.xcframework/.+)$", (root/'BUILD-INFO.txt').read_text(), re.M)
assert len(records)==14
for expected, relative in records:
    assert hashlib.sha256((root/relative).read_bytes()).hexdigest()==expected, relative
out={'slices':rows,'failures':fail,'upstream_record_hashes_verified':len(records),'passed':not fail}
print(json.dumps(out,indent=2))
assert not fail, fail
