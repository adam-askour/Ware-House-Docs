# Secure implementation assumptions

1. Development may use SQLite for a runnable local process; integrated and
   production-style operation uses PostgreSQL.
2. TLS is terminated by the included Nginx configuration or an organizational
   reverse proxy. Plain HTTP is development-only.
3. ClamAV may be unavailable during development; later ingestion code will
   expose this degraded state and quarantine or fail closed according to the
   selected environment policy.
4. Physical storage paths are never user-facing and protected media has no
   public URL.
5. Arabic prototype search uses normalized exact tokens. Advanced morphology is
   explicitly deferred by the requirements.
6. Real scanner capabilities remain unknown. Only the simulator and a
   replaceable ingestion adapter will be implemented.
