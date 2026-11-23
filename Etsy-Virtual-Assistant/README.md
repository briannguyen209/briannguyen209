# Etsy Virtual Assistant

An AI assistant (built with Claude) for the **NostalGiftShop** Etsy shop (embroidered/printed apparel and posters).

## Goals

1. **Stop answering the same questions over and over.** The assistant reads a customer message, checks the knowledge base and past conversations, and writes a reply in the shop owner's voice.
2. **Never miss a message.** New messages should trigger alerts, plus reminders if they stay unanswered.
3. **Human approval when uncertain.** If the answer isn't clearly supported by the knowledge base (or involves mistakes, refunds, custom requests, unhappy customers), the assistant only **drafts** the reply and waits for approval. It must never send it.
4. **Automatic responses are strongly wanted** for confident answers. See the constraints below.

## What we've learned so far

### Etsy API: no messaging
- Etsy Open API v3 supports listings, orders, shipping and reviews, but **does not have endpoints to read or send Convos (messages)**, as of Nov 2026. A seller feature request from March 2026 had no response.
- The API can still be used later for **listings/catalog data and order/tracking lookups**.

### Gmail notifications: no message content
- Etsy message notifications arrive in Gmail, but they **don't include the message text**. They can only be used as a "new message" signal and to trigger reminders, not as the source for drafting replies.

### Past conversations: available
- They come from **Your account → Account settings → Privacy → Download data**, in a ZIP that arrives by email. The link expires after 2 weeks.
- This is not the same as Shop Manager → Settings → Options → Download Data, which only has orders and listings.
- The ZIP contains a **JSON file of convos**. Each record looks like this:
  ```json
  {"Date":"2026-11-20","Sender":"<customer first name>","Recipient":"Nosta","Subject":"...","Content":"...","images":"<etsystatic image URL or empty>"}
  ```
- The shop's sender name is **`Nosta`**.

### Notes for parsing the convos JSON
- **No conversation/thread ID.** Group threads by the other party's name + nearby dates. Watch for two customers with the same first name.
- **Dates only, no times.** Within a day, keep the order from the file.
- `Subject` duplicates `Content`. Use `Content`.
- Some records have empty `Content` and only an `images` URL (the customer sent a photo). Record it as "customer sent a photo".
- The pasted sample was a run of JSON objects with no commas or array brackets. The parser must handle concatenated objects (e.g. `json.JSONDecoder.raw_decode` in a loop).
- **Privacy:** strip customer names, order numbers and tracking numbers before building the knowledge base. Never commit `data/raw/` or `data/processed/` to git.

### Common question types (from the first sample)

| Type | Example | Handling |
|---|---|---|
| Size availability | "Do you have 3XL in Comfort Colors?", "3–5XL for this design?" | ✅ Auto, once the catalog lists sizes, colors and brands |
| Where to buy / listing links | Sending links to other prints or the 3XL listing | ✅ Auto, needs the current listing links in the catalog |
| Wrong or missing personalization | Names missing from a sleeve; "auntie" sent instead of "mama" | ⚠️ Draft only: apologize, offer a replacement or partial refund |
| Replacement tracking / delivery timing | "Will I get a new tracking number?", "Will it arrive by Thursday?" | ⚠️ Draft only: needs real tracking info |

Known facts so far (confirm and extend in `catalog/` and `knowledge-base/`):
- Larger sizes: **Gildan sweaters in 3–5XL** in black, sport grey, navy, royal blue and dark heather. The customer orders the large-size listing and leaves a note/personalization for the design, or messages back with the order #.
- Comfort Colors 3XL tees are available through a separate listing.
- For shop mistakes, the owner usually lets the customer **keep the wrong item** and sends a replacement, then sends the new tracking link once shipped.

### Owner's voice / tone
Short, warm, apologetic for mistakes, e.g. *"Oh no, I'm so sorry for the oversight!"*, *"Thanks for your understanding and patience."* Often includes a direct listing link. Ends with "Thanks" / "Thank you".

## Options for sending and receiving messages

| Option | How | Automatic? | Risk |
|---|---|---|---|
| **A. Chrome extension** (leading candidate) | When the owner opens a convo on etsy.com, the extension reads the page, drafts a reply into the box and labels it ✅ Confident / ⚠️ Needs review. The owner clicks Send. It can also save each opened convo to grow the knowledge base. | Semi (one click) | Low: reads only the page being viewed, never sends on its own. Desktop only. |
| **B. Browser automation bot** | Logged-in script polls the inbox, auto-sends confident replies, saves the rest as drafts | Full | **High**: likely breaks Etsy's rules on automated access; shop warning or suspension is possible; fragile |
| **C. Copy-paste web page** | Paste a message, get a reply, paste it back | Manual | None |
| **Add-on: Gmail watcher** | Uses Etsy notification emails to alert and send reminders for unanswered messages | n/a | None |

**Current plan:** process the convos JSON first, then decide on Option A (plus the Gmail reminder add-on). Option B could be added later and reuse the same knowledge base and reply logic.

## Assistant logic (planned)
1. Input: customer message (+ thread history).
2. Retrieve: matching knowledge-base entries, catalog rows and similar past Q&A pairs.
3. Claude drafts a reply in the owner's voice, using only retrieved facts.
4. Classify confidence. Mark **Needs review** (with a reason) when info is missing or conflicting, the customer is upset, or the message involves mistakes, refunds, discounts, custom orders, delivery promises or photos.
5. Optional: order and tracking lookup through the Etsy API.

## Folder structure

```
Etsy-Virtual-Assistant/
├── README.md                 - this file
├── .gitignore                - excludes data/raw, data/processed, drafts
├── data/
│   ├── raw/                  - Etsy data export (convos JSON). PRIVATE
│   └── processed/            - cleaned threads, grouped questions
├── knowledge-base/
│   ├── policies/             - shipping.md, returns-and-mistakes.md, personalization.md
│   └── faq/                  - common questions + approved answers
├── resources/
│   ├── size-charts/          - size chart images
│   ├── product-photos/       - one subfolder per product
│   └── variations/           - brand / color / size charts
├── catalog/
│   └── products.csv          - listing_title,listing_url,product_type,brand,sizes,colors,price_notes,notes
├── drafts/                   - replies waiting for approval
└── app/                      - assistant code (extension, scripts)
```

## Next steps
1. [ ] Put the full convos JSON in `data/raw/`.
2. [ ] Write a parser that turns it into clean threads in `data/processed/` (handle the issues listed above).
3. [ ] Group the questions by type, count how often each comes up, and pull out the owner's best answers. Present a summary to the owner.
4. [ ] Add size charts, product photos and variation charts to `resources/`. Turn them into `catalog/products.csv` and the FAQ.
5. [ ] Fill in the policy templates in `knowledge-base/policies/`.
6. [ ] Decide on Option A, then build a prototype in `app/`.
7. [ ] Add the Gmail reminder for unanswered messages.

## Caveat
This folder is on a work (Government of Ontario) OneDrive. The owner has acknowledged that it holds personal-business customer data and chose to keep it there.
