# E-Commerce Full Stack Platform

A portfolio-oriented e-commerce starter built with React + Vite + TypeScript, Django REST Framework, PostgreSQL, optional MongoDB activity logging, and Docker Compose.

## Features
- JWT registration/login/refresh; customer/admin roles and protected API operations.
- Product/category catalog, search/filter/sort/pagination, stock tracking.
- Persistent cart, backend price/stock validation, transaction-safe checkout.
- Order history/detail/cancellation; mock payment clearly labelled.
- Admin summary, product/category/order management endpoints.
- MongoDB product-view/search activity events; graceful fallback if MongoDB is unavailable.
- Swagger/OpenAPI at `/api/docs/`, schema at `/api/schema/`.
- Health endpoint at `/api/health/`.
- Responsive React pages for catalog, product detail, auth, cart, checkout, orders, profile, and admin.
- Backend tests and frontend component test setup.

## Run on Windows (PowerShell)
1. Install Docker Desktop and start it.
2. Copy `.env.example` to `.env` and change `DJANGO_SECRET_KEY` for anything beyond local development.
3. From this folder run:
   ```powershell
   Copy-Item .env.example .env
   docker compose up --build
   ```
4. In another terminal, create an admin:
   ```powershell
   docker compose exec backend python manage.py createsuperuser
   ```
5. Open:
   - Frontend: http://localhost:5173
   - API: http://localhost:8000/api/
   - Swagger: http://localhost:8000/api/docs/
   - Django admin: http://localhost:8000/admin/
   - Health: http://localhost:8000/api/health/

The backend container generates the store app migration and runs migrations on startup. Product data is initially empty; create products via Django admin or the API as an admin.

## Useful commands
```powershell
docker compose up -d --build        # build and start
docker compose ps                   # inspect services
docker compose logs -f backend      # follow backend logs
docker compose logs -f frontend     # follow frontend logs
docker compose exec backend python manage.py test
docker compose exec frontend npm test -- --run
docker compose down                 # stop, keep volumes
docker compose down -v              # stop and DELETE local database volumes
docker compose restart backend
```

## API overview
- `POST /api/auth/register/`
- `POST /api/auth/token/`, `POST /api/auth/token/refresh/`
- `GET/PATCH /api/profile/`
- `GET /api/categories/`
- `GET /api/products/` (query: `search`, `category`, `min_price`, `max_price`, `available`, `ordering`, `page`)
- `GET /api/products/{id}/`; admin `POST/PATCH/DELETE` on products
- `GET/POST /api/cart/`, `PATCH/DELETE /api/cart/{item_id}/`
- `POST /api/checkout/` (optional `Idempotency-Key` header)
- `GET /api/orders/`, `GET /api/orders/{id}/`, `POST /api/orders/{id}/cancel/`
- `GET /api/admin/summary/`

## Security and production notes
- Checkout uses PostgreSQL `transaction.atomic()` and row locks, recalculates totals from server-side product prices, and decrements inventory only after validation.
- Duplicate checkout submissions with the same `Idempotency-Key` return the existing order.
- Payment is a **mock payment** only; no card details are collected. Add a real provider and verified webhooks before accepting money.
- Set `DEBUG=False`, a strong secret, explicit `ALLOWED_HOSTS`, HTTPS, secure cookies/proxy settings, backups, monitoring, and rate limiting before deployment.
- MongoDB stores limited event metadata only. It never stores passwords, JWTs, or payment details. Logging failure does not block shopping.
- The included test suite covers core API behavior but does not replace security review, load testing, or integration tests against every deployment environment.

## Environment
See `.env.example`. `MONGO_ENABLED=false` disables MongoDB event writes. For local testing, PostgreSQL is the configured application database.
