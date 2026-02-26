# 🌸 Parfume Center — Mini App Setup Guide

## What you'll have
A beautiful shop UI that opens **inside Telegram** when users tap "🛍 Open Shop".
Customers browse products, add to cart, and checkout — all without leaving Telegram.

---

## Step 1 — Host the Mini App on GitHub Pages (Free, 5 min)

GitHub Pages gives you a free HTTPS URL, which Telegram requires.

1. Go to **github.com** and create a free account if you don't have one
2. Click **"New repository"** (green button)
3. Name it: `parfume-shop`
4. Set it to **Public**
5. Click **"Create repository"**
6. Click **"uploading an existing file"**
7. Drag and drop your `index.html` file
8. Click **"Commit changes"**
9. Go to **Settings → Pages** (left sidebar)
10. Under "Source" select **"Deploy from branch"** → **main** → **/ (root)**
11. Click **Save**
12. Wait ~60 seconds, then your URL will appear:
    `https://YOUR_USERNAME.github.io/parfume-shop/`

---

## Step 2 — Update config.py

Open `config.py` and set:
```python
BOT_TOKEN  = "your_token_from_botfather"
ADMIN_IDS  = [your_telegram_id]         # integer, no quotes
WEBAPP_URL = "https://YOUR_USERNAME.github.io/parfume-shop/"
```

---

## Step 3 — Register Mini App with BotFather

1. Open **@BotFather** in Telegram
2. Send `/newapp` (or `/mybots` → select your bot → **Bot Settings → Menu Button**)
3. Follow the steps and paste your GitHub Pages URL
4. **Or** just use `/setmenubutton`:
   - Send `/setmenubutton`
   - Select your bot
   - Send the URL: `https://YOUR_USERNAME.github.io/parfume-shop/`
   - Send the button title: `🛍 Shop`

---

## Step 4 — Install & Run

```bash
pip install aiogram==3.13.1
python bot.py
```

---

## Step 5 — Test it!

1. Find your bot on Telegram
2. Send `/start`
3. Tap **"🛍 Open Shop"**
4. Browse, add to cart, checkout 🎉

---

## Updating Products

To change products/prices, open `index.html` and edit the `products` array (around line 220):

```javascript
const products = [
  {
    id: 1, catId: '1', name: 'Rose Elixir', vol: '50ml EDP',
    emoji: '🌹', price: 89.99, badge: 'Bestseller',
    desc: 'Your description here...',
    notes: ['Rose', 'Peach', 'Musk'],
  },
  // add more products here...
];
```

Then re-upload `index.html` to GitHub and changes go live in ~30 seconds.

---

## Adding Real Product Photos

Replace the emoji in the product card with an `<img>` tag. In `index.html`, in the `productCardHTML` function, change:
```html
<span>${p.emoji}</span>
```
to:
```html
<img src="${p.image}" alt="${p.name}" />
```

And add an `image` field to each product:
```javascript
{ id: 1, ..., image: 'https://your-cdn.com/rose-elixir.jpg' }
```

Upload images to GitHub too, then reference them as:
`https://YOUR_USERNAME.github.io/parfume-shop/images/rose.jpg`

---

## How Orders Work

1. Customer fills out checkout in the Mini App
2. Data is sent to your bot via `tg.sendData()`
3. Bot sends customer a confirmation message
4. Bot sends YOU (admin) a notification with action buttons
5. You tap ✅ Confirm / 🚚 Shipped / 🎉 Delivered
6. Customer gets automatically notified each time
