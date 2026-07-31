# Local TLS certificates

Place a locally trusted `dms.crt` and its protected `dms.key` here for the
production-style local deployment. Do not commit certificate private keys.
An organization reverse proxy may terminate TLS instead, but traffic from
browsers to that proxy must remain HTTPS.
