$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\env.ps1"
$context = 'E:\CSC2108Local\judge-build'
New-Item -ItemType Directory -Force -Path $context | Out-Null
# Export public Windows trust certificates only; TLS verification remains enabled.
@'
import ssl
from pathlib import Path
certificates = []
for store in ('ROOT', 'CA'):
    for cert, encoding, trust in ssl.enum_certificates(store):
        if encoding == 'x509_asn' and (trust is True or '1.3.6.1.5.5.7.3.1' in trust):
            certificates.append(ssl.DER_cert_to_PEM_cert(cert))
Path('E:/CSC2108Local/judge-build/host-ca.pem').write_text(''.join(sorted(set(certificates))), encoding='ascii')
'@ | & 'E:\CSC2108Local\.venv\Scripts\python.exe' -
if ($LASTEXITCODE -ne 0) { throw 'Public trust certificate export failed' }
Copy-Item -LiteralPath "$PSScriptRoot\judge.Dockerfile" -Destination "$context\Dockerfile" -Force
Copy-Item -LiteralPath "$PSScriptRoot\judge-requirements.lock" -Destination "$context\judge-requirements.lock" -Force
docker build -t csc2108-lcb-judge:v1 $context
if ($LASTEXITCODE -ne 0) { throw 'Judge image build failed' }
