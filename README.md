# E-Commerce REST and GraphQL API
A full-featured e-commerce API with product catalog, shopping cart, checkout via Stripe, and order management — available over both REST and GraphQL.

## Features
- **Product catalog** — create, search, filter, and sort products by category and price
- **Redis caching** — product endpoints are cached to reduce database load
- **Shopping cart** — add, update, and remove items with stock validation
- **Checkout via Stripe** — create payment intents and handle webhook events to confirm orders
- **Order management** — view order history and individual order details per user
- **Authentication** — JWT-based auth with admin role support
- **GraphQL** — query products, categories, and orders; update order status via mutation

## Tech Stack
- **Python** — language
- **FastAPI** — web framework
- **SQLAlchemy** — ORM
- **SQLite** — database
- **Pydantic** — request/response validation
- **Strawberry** — GraphQL library
- **Redis** — caching
- **Stripe** — payment processing
- **Jose** — JWT token handling
- **Uvicorn** — ASGI server
- **Pytest** — testing

## Architecture Overview
The API is split into REST routes and a GraphQL schema. REST routes handle all write operations (create, update, delete) and cart/checkout flows. GraphQL handles read operations for products, categories, and orders.

Authentication uses JWT tokens. The `get_current_user` dependency decodes the token and injects the user into every protected route. Admin-only endpoints check `user.is_admin` before proceeding.

Stripe checkout uses a two-step flow: the client calls `POST /checkout` to create a PaymentIntent, then confirms payment on the frontend. Once payment succeeds, Stripe sends a webhook to `POST /checkout/webhook` which creates the order, deducts stock, and clears the cart.

## API Documentation

### Auth
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login and receive a JWT token |

### Products
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/products` | Get all products (public) |
| GET | `/products/{product_id}` | Get a single product (public) |
| POST | `/products` | Create a product (admin only) |
| PUT | `/products/{product_id}` | Update a product (admin only) |
| DELETE | `/products/{product_id}` | Delete a product (admin only) |

Query parameters for `GET /products`:
- `search` — filter by product name (case-insensitive)
- `category_id` — filter by category
- `sort` — `price_asc` or `price_desc`

### Categories
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/categories` | List all categories (public) |
| GET | `/categories/{category_id}` | Get a single category (public) |
| POST | `/categories` | Create a category (admin only) |
| PUT | `/categories/{category_id}` | Update a category (admin only) |
| DELETE | `/categories/{category_id}` | Delete a category (admin only) |

### Cart
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/carts` | Get the current user's cart |
| POST | `/carts/items` | Add a product to the cart |
| PUT | `/carts/items/{item_id}` | Update quantity of a cart item |
| DELETE | `/carts/items/{item_id}` | Remove an item from the cart |

### Checkout
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/checkout` | Create a Stripe PaymentIntent |
| POST | `/checkout/webhook` | Stripe webhook — creates order on payment success |

### Orders
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/orders` | Get all orders for the current user |
| GET | `/orders/{order_id}` | Get a single order |

### GraphQL — `/graphql`
**Queries:**
- `products` — list all products
- `product(id)` — get a single product
- `categories` — list all categories
- `category(id)` — get a single category

**Mutations:**
- `update_order_status(orderId, status)` — update the status of an order

## Setup Instructions

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd E-commerce-REST-and-GraphQL-API
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the project root:
```
SECRET_KEY=your_secret_key
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret
```

### 5. Start Redis
```bash
redis-server
```

### 6. Run the server
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`. The GraphQL playground is at `http://localhost:8000/graphql`.

## Running Tests
```bash
pytest
```
