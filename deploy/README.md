# Public demo

The search engine online, on a free server. One container (`Dockerfile`) holds Elasticsearch,
listening only inside the container, and the web app; Caddy (`compose.yaml`) is the only service
reachable from outside and serves HTTPS with a free Let's Encrypt certificate. Everything is built
from the repository and from public sources: the Wikinews dump from Wikimedia, the embedding model
from Hugging Face; the indices are built once, while the image is built (about 10 minutes, and
about 10 GB of free disk during the build).

Server used: an Oracle Cloud **Always Free** machine (Ampere A1, ARM, 2 OCPU and 12 GB of RAM out
of the 4 and 24 that are free). The same files work on any Linux machine with Docker and about
4 GB of free RAM.

## Steps

1. Oracle Cloud console: create a Compute instance with image Canonical Ubuntu 24.04, shape
   VM.Standard.A1.Flex (2 OCPU, 12 GB), a public IPv4 address and your SSH public key.
2. In the virtual cloud network of the instance, security list: add two ingress rules, TCP 80
   and TCP 443 from 0.0.0.0/0.
3. On the machine (`ssh ubuntu@<ip>`):

   ```bash
   sudo apt-get update && sudo apt-get install -y docker.io docker-compose-v2 git
   sudo iptables -I INPUT 6 -p tcp -m multiport --dports 80,443 -m state --state NEW -j ACCEPT
   sudo netfilter-persistent save
   git clone https://github.com/dnlsdn/wikinews-search.git && cd wikinews-search
   sudo DOMAIN=<ip with dashes>.sslip.io docker compose -f deploy/compose.yaml up -d --build
   ```

   The Ubuntu images of Oracle Cloud reject every port but 22 in `iptables`: the second command
   opens 80 and 443, the third keeps the rule after a reboot. `sslip.io` is a free DNS name that
   points to the IP written in it (`1-2-3-4.sslip.io` -> 1.2.3.4), so Caddy can get a certificate
   without buying a domain.
4. Check: `sudo docker compose -f deploy/compose.yaml logs -f app` until "warm-up done", then open
   `https://<ip with dashes>.sslip.io`.

To update after a push: `git pull`, then the same `docker compose ... up -d --build`.

## Test on a laptop

From the root of the repository: `docker build -f deploy/Dockerfile -t wikinews-demo .`, then
`docker run -p 7860:7860 wikinews-demo` and open http://localhost:7860. It needs about 10 GB of
free disk while it builds.
