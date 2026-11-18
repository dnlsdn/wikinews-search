# Public demo

The search engine online. One container (`Dockerfile`) holds Elasticsearch, listening only inside
the container, and the web app; Caddy (`compose.yaml`) is the only service reachable from outside
and serves HTTPS with a free Let's Encrypt certificate. The image is built from the repository
files and from public sources: the Wikinews dump from Wikimedia and the embedding model from
Hugging Face. The indices are built once, while the image is built (about 15 minutes, and about
10 GB of free disk during the build).

## Where it runs

An Azure virtual machine paid by the Azure for Students credit (no credit card): size
Standard_B2als_v2 (2 vCPU, 4 GB of RAM, x86), Ubuntu 24.04, 30 GB Standard SSD, region Denmark
East (the student subscription allows only a few European regions, and the smaller sizes were not
available in the others on 18 November 2026). About 40 dollars a month of credit with the disk and
the public address, so the 100 dollars last until about February; when the credit ends the machine
is switched off, nothing is charged. A 2 GB swap file is added because 4 GB of RAM is just enough
for Elasticsearch (1 GB heap) and the embedding model.

Address: https://wikinews-search.denmarkeast.cloudapp.azure.com (a free host name given by Azure).

## Steps

1. Machine (Azure CLI, after `az login`):

   ```bash
   az group create -n wikinews -l denmarkeast
   az vm create -g wikinews -n wikinews --image Canonical:ubuntu-24_04-lts:server:latest \
     --size Standard_B2als_v2 --admin-username ubuntu --ssh-key-values <public key> \
     --public-ip-sku Standard --public-ip-address-dns-name wikinews-search \
     --storage-sku StandardSSD_LRS --os-disk-size-gb 30 --nsg-rule SSH
   az vm open-port -g wikinews -n wikinews --port 80,443 --priority 1010
   ```

2. On the machine: swap and Docker.

   ```bash
   sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile
   sudo swapon /swapfile && echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab
   sudo apt-get update && sudo apt-get install -y docker.io docker-compose-v2
   ```

3. The code: `git clone` of this repository on the machine (or, from a laptop with the
   repository, `git archive main | ssh ubuntu@<host> "mkdir -p wikinews-search && tar -x -C wikinews-search"`).
4. Build and start:

   ```bash
   cd wikinews-search
   sudo DOMAIN=<host name> docker compose -f deploy/compose.yaml up -d --build
   ```

5. Check: `sudo docker compose -f deploy/compose.yaml logs -f app` until "warm-up done", then open
   `https://<host name>`.

To update: copy the new code, then the same `docker compose ... up -d --build`. The same files work
on any Linux machine with Docker, 4 GB of RAM and swap (for example an Oracle Cloud Always Free
Ampere machine, when one is available: the image builds on ARM too).

## Test on a laptop

From the root of the repository: `docker build -f deploy/Dockerfile -t wikinews-demo .`, then
`docker run -p 7860:7860 wikinews-demo` and open http://localhost:7860. It needs about 10 GB of
free disk while it builds.
