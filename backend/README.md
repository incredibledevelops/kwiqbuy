# KwiqBuy — Multi-Vendor Marketplace API

FastAPI + MongoDB (Beanie) + Paystack backend for the KwiqBuy marketplace.

## Features

- Multi-vendor: customers order from multiple vendors in one checkout
- Vendor portal: product CRUD, order fulfillment, analytics, payouts
- Admin portal: vendor approvals, commission config, audit log, payouts
- Rider portal: claim orders, multi-vendor pickups, delivery status
- Customer portal: order history, address book, favorites, referrals
- Loyalty program, promo codes (platform + vendor-scoped), referrals
- Paystack payments + payouts (transfers to vendor recipients)
- MongoDB transactions (replica set required in production)
- Audit log for every state change

## Tech Stack

- **FastAPI** — async REST API
- **PyMongo + Beanie** — async MongoDB ODM (2.x)
- **Pydantic v2** — validation & settings
- **Paystack** — payments + transfers (MoMo, card, bank)
- **JWT** — auth (staff / vendor / rider / admin); OTP for customers
- **Pillow** — image optimization + EXIF stripping
- **Redis** — response caching

## Quick Start

```bash
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d mongo redis
python -m scripts.seed_data
uvicorn app.main:app --reload