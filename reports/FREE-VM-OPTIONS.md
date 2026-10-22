# Big-Compute Options for CPU-Heavy Builds

Target spec: 64 vCPU, 256 GB RAM, 1 TB disk. Nothing free reaches this, so the list starts with the best free options and then moves to credits and cheap paid hardware. Prices are from sources checked in October 2026 and can change.

## 1. Oracle Cloud Always Free (free, persistent)

- **Specs:** up to 4 Arm Ampere A1 cores, 24 GB RAM, about 200 GB storage. Usable as one VM or up to 4 smaller VMs.
- **Good for:** an always-on server you can log into and use like a normal machine.
- **Catch:** Arm (ARM64), so some images and tools may not work. A card is required for sign-up. Idle instances can be reclaimed if CPU and memory use stay under 20% for 7 days. Capacity is sometimes hard to get.

## 2. GitHub Actions on a public repo (free, temporary)

- **Specs:** 4 vCPU, 16 GB RAM, 14 GB SSD (x64 or Arm). Free and unlimited for public repositories. Docker works. Jobs can run up to 6 hours.
- **Good for:** building and testing images and code in CI.
- **Catch:** the repo must be public (private repos get 2 vCPU / 8 GB and count against a monthly quota). Each job starts on a fresh VM, and 14 GB of disk is small.

## 3. Trial credits (free for a limited time)

- **AWS:** up to about $200 over roughly 6 months.
- **Oracle Cloud:** $300 for 30 days.
- **Google Cloud:** about $300 for 90 days.
- **Good for:** a few days of a 64 vCPU machine at no cost.
- **Catch:** new accounts often have vCPU quotas that block very large instances, so you may need to request an increase.

## 4. AWS spot instances (cheapest large machines)

| Instance | vCPU / RAM | Spot price (approx.) | On-demand |
| --- | --- | --- | --- |
| c7g.16xlarge (Arm) | 64 / 128 GB | about $0.63/hr | $2.32/hr |
| c7a.16xlarge (x64) | 64 / 128 GB | about $0.94/hr (cheapest region) | $3.28/hr |
| c7a.32xlarge (x64) | 128 / 256 GB | about $1.09/hr | $6.57/hr |

- **Good for:** short, heavy builds. The c7a.32xlarge exceeds your CPU and RAM target for about a dollar an hour.
- **Catch:** spot instances can be interrupted at short notice. Storage is separate (EBS), so a 1 TB disk adds a monthly charge (roughly $80/month, not verified). Delete the disk when you are finished.

## 5. Hetzner Cloud CCX63 (simplest paid option)

- **Specs:** 48 dedicated vCPU, 192 GB RAM, 960 GB SSD. This is the closest match to your target spec.
- **Price:** about EUR 288/month, or about EUR 0.46/hour. Billing is hourly with a monthly cap.
- **Good for:** a few hours of builds costs a couple of euros. No spot interruptions.
- **Catch:** sources disagree on the current price (one lists about $374/month) after the April 2026 price increase. Check the console before you commit. Hetzner Cloud tops out at 48 vCPU.

## Quick pick

- Always-on and free: Oracle Always Free, plus GitHub Actions for burst builds.
- One-off heavy job, cheapest: AWS spot c7a.32xlarge, then delete everything.
- One-off heavy job, simplest: Hetzner CCX63, delete the server afterwards.
- Try big hardware for free: use trial credits, and ask for a quota increase if the instance is blocked.
