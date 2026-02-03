# GHL Automation Workflows for Facebook Ad Tracking
**The Jorge Ramirez Group - Complete Implementation Guide**

Track every Facebook ad click, capture leads automatically, and nurture them without lifting a finger.

---

## 🎯 OVERVIEW

This document covers **5 core workflows** that work together:

1. **Seller Guide Download Trigger** → Tags contact, starts nurture sequence
2. **Facebook Ad Click Tracker** → Captures source, campaign, ad ID
3. **Listing Page View Tracker** → Knows which homes they viewed
4. **Auto-Response Handler** → Instant reply to messages/calls
5. **Retargeting Pixel Sync** → Sends data back to Facebook for Custom Audiences

---

## 📊 WORKFLOW 1: Seller Guide Download Trigger

**Purpose**: Tag and nurture anyone who downloads your Seller's Guide  
**Trigger**: Form submission on value.thejorgeramirezgroup.com  
**Goal**: Move them from "Curious" to "Ready to List"

### Setup in GHL:

**Automation → Create New Workflow → "Seller Guide Download"**

#### Trigger:
- Form Submitted: "Seller Guide Download Form"
- OR Tag Added: "Downloaded Seller Guide"

#### Actions (in order):

**1. Add Tags**
```
Tags to add:
- "Lead Source: Seller Guide"
- "Stage: Awareness"
- "Temperature: Warm"
- "Last Activity: [Today's Date]"
```

**2. Send Immediate Email**
```
Subject: Your Seller's Guide is Here 📖
From: Jorge Ramirez <jorge@thejorgeramirezgroup.com>

Body:
Hey [First Name],

Thanks for downloading the guide! It should be in your inbox right now (check spam if you don't see it).

Quick question: what made you request it today? Genuinely curious what you're working through right now.

If you want to talk through anything in the guide—pricing, timing, what to fix before listing, whatever—text me anytime: 908-230-7844

No sales pitch. Just helpful answers.

— Jorge

P.S. I'll check in again in a few days to see if you have questions.
```

**3. Wait 3 Days**

**4. Send Follow-Up Email**
```
Subject: What surprised you in the guide?
From: Jorge Ramirez

Body:
[First Name],

Most people who download the seller's guide tell me one section changed how they think about listing.

Was it the pricing strategy? The marketing timeline? Something else?

Curious what stood out to you.

If you want to dig deeper into anything, let's talk: 908-230-7844

— Jorge
```

**5. Wait 4 Days**

**6. Send Final Nudge**
```
Subject: Still thinking about it?
From: Jorge Ramirez

Body:
[First Name],

You grabbed the seller's guide about a week ago.

Maybe you're still weighing your options. Maybe life got busy. Maybe you're not ready yet.

That's totally fine.

But if you have questions—about pricing, timing, what to fix before listing, whatever—I'm here. No pitch. Just honest answers.

Text me: 908-230-7844

— Jorge

P.S. If you're not ready to list yet, that's cool. I'll stop bugging you. Just reply "not yet" and I'll check back in 3 months.
```

**7. Create Task for Jorge**
```
Task: "Follow up with [First Name] - Downloaded Seller Guide 7 days ago, no response"
Assigned to: Jorge Ramirez
Due: Today
```

---

## 🎯 WORKFLOW 2: Facebook Ad Click Tracker

**Purpose**: Capture which Facebook ad brought them to your site  
**Trigger**: Landing page visit with Facebook UTM parameters  
**Goal**: Know which ads work best + personalize follow-up

### Setup:

**Step 1: Add UTM Parameters to Every Facebook Ad**

In Facebook Ads Manager, for each ad's URL, append:

```
?utm_source=facebook
&utm_medium=cpc
&utm_campaign=[Campaign Name]
&utm_content=[Ad Name]
&fbclid={{ad.id}}
```

**Example**:
```
https://thejorgeramirezgroup.com/how-we-sell-your-home.html?utm_source=facebook&utm_medium=cpc&utm_campaign=Seller_Retargeting_Days1-3&utm_content=Ad1B_SocialProof&fbclid={{ad.id}}
```

**Step 2: Create Workflow in GHL**

**Automation → Create New → "Facebook Ad Click Tracker"**

#### Trigger:
- Form Submitted (any form)
- OR Page Visited: Any page with "utm_source=facebook"

#### Actions:

**1. Add Custom Field Values**
```
Custom Fields to Update:
- Lead Source: "Facebook Ad"
- Campaign: [Extract from utm_campaign]
- Ad Name: [Extract from utm_content]
- Ad Click Date: [Today]
```

**2. Add Tags Based on Campaign**

If `utm_campaign` contains "Seller_Retargeting":
- Add tag: "Facebook: Seller Retargeting"

If `utm_campaign` contains "Listing_Retargeting":
- Add tag: "Facebook: Listing Retargeting"

If `utm_content` contains "Ad1A":
- Add tag: "Ad Type: Curiosity Hook"

If `utm_content` contains "Ad1B":
- Add tag: "Ad Type: Social Proof"

(Add more conditions for each ad template)

**3. Send Internal Notification**
```
Slack/SMS to Jorge:
"🔥 New Facebook ad click!
Name: [First Name] [Last Name]
Campaign: [Campaign Name]
Ad: [Ad Name]
Page: [Page URL]
Time: [Timestamp]"
```

**4. Trigger Ad-Specific Follow-Up**

If Ad Type = "Social Proof":
- Wait 1 hour
- Send SMS: "Hey [First Name], saw you checked out the 3 homes we just sold. Thinking about listing soon? - Jorge"

If Ad Type = "Curiosity Hook":
- Wait 2 hours
- Send SMS: "Hey [First Name], curious what stood out to you in the seller's guide. Want to chat about it? Text back anytime. - Jorge"

---

## 🏠 WORKFLOW 3: Listing Page View Tracker

**Purpose**: Know which listings prospects viewed  
**Trigger**: Page view on specific listing URL  
**Goal**: Retarget with that exact listing, send alternatives

### Setup:

**Step 1: Add Tracking Pixel to Every Listing Page**

In GHL → Settings → Tracking Code, create:

```html
<!-- Listing Page Tracker -->
<script>
  // Capture listing address from page
  var listingAddress = document.querySelector('h1').innerText; // Adjust selector as needed
  
  // Send to GHL via webhook
  fetch('https://services.leadconnectorhq.com/hooks/[YOUR_WEBHOOK_ID]', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contactId: '[Contact ID]', // From cookie or URL param
      listingAddress: listingAddress,
      listingURL: window.location.href,
      timestamp: new Date().toISOString()
    })
  });
</script>
```

**Step 2: Create Webhook in GHL**

**Automation → Webhooks → Create New**

Name: "Listing View Capture"  
Trigger: Incoming webhook data  

**Step 3: Create Workflow**

**Automation → Create New → "Listing Page View Handler"**

#### Trigger:
- Webhook Received: "Listing View Capture"

#### Actions:

**1. Add Custom Field**
```
Custom Field: "Last Listing Viewed"
Value: [Listing Address from webhook]

Custom Field: "Last Listing View Date"
Value: [Today]
```

**2. Add Tag**
```
Tag: "Viewed Listing: [Listing Address]"
```

**3. Wait 1 Day**

**4. If No Showing Booked, Send SMS**
```
SMS to Contact:
"Hey [First Name], you checked out [Listing Address] yesterday. Still interested? Want to see it this weekend? - Jorge"
```

**5. Wait 3 Days**

**6. If Still No Showing, Send Follow-Up**
```
SMS:
"[First Name], what stopped you on [Listing Address]? Was it the price, location, or just not quite right? Genuinely curious. - Jorge"
```

**7. Wait 4 Days**

**8. Send Alternative Listings**
```
SMS:
"Hey [First Name], if [Original Listing] wasn't the one, I have 3 other homes in [Town] you might like. Want me to send them? - Jorge"
```

---

## 💬 WORKFLOW 4: Auto-Response Handler

**Purpose**: Instant reply to every Facebook Messenger / Instagram DM / SMS  
**Trigger**: Inbound message from any channel  
**Goal**: Never miss a lead, reply within 60 seconds

### Setup:

**Automation → Create New → "Instant Response - All Channels"**

#### Trigger:
- Inbound Message Received
- From: Facebook Messenger, Instagram DM, SMS, or WhatsApp

#### Conditions:

**IF** message contains keywords: "price", "cost", "how much", "listing":
→ Route to **Pricing Question Flow**

**IF** message contains keywords: "showing", "tour", "see", "visit":
→ Route to **Showing Request Flow**

**IF** message contains keywords: "sell", "list", "agent", "help":
→ Route to **Seller Inquiry Flow**

**ELSE**:
→ Route to **General Inquiry Flow**

---

### Sub-Flow 4A: Pricing Question

**1. Send Immediate Reply**
```
SMS/Messenger:
"Hey [First Name]! Good question about pricing. Which property are you asking about? I'll get you exact numbers in 2 min."
```

**2. Create Task for Jorge**
```
Task: "Reply to [First Name] about pricing on [Property]"
Due: In 5 minutes
```

**3. Wait 5 Minutes**

**4. If Jorge Hasn't Replied, Send Auto-Response**
```
"Hey [First Name], Jorge here. For [Property Address], current price is $XXX,XXX. Want to know more about it? Text me back or call: 908-230-7844"
```

---

### Sub-Flow 4B: Showing Request

**1. Send Immediate Reply**
```
"Great! I can definitely get you in to see it. What day/time works best for you this week?"
```

**2. Wait for Reply (with 4-hour timeout)**

**3. If Reply Received:**
- Add tag: "Requested Showing"
- Create calendar event (tentative)
- Send confirmation SMS: "Got it! I'll confirm [Day] at [Time] and text you the details within the hour."

**4. If No Reply in 4 Hours:**
- Send follow-up: "Hey [First Name], still want to see [Property]? I have openings Saturday 10am or Sunday 2pm. Which works?"

---

### Sub-Flow 4C: Seller Inquiry

**1. Send Immediate Reply**
```
"Hey [First Name]! Happy to help. Quick question: are you thinking about selling soon, or just exploring your options right now?"
```

**2. Wait for Reply**

**3. Based on Response:**

If "soon" or "ready":
- Add tag: "Hot Seller Lead"
- Send: "Perfect. Want to hop on a quick call this week to talk through pricing and timeline? Or would you rather I send you a free home value estimate first?"

If "exploring" or "not sure":
- Add tag: "Warm Seller Lead"
- Send: "Totally understand. No pressure. Want me to send you a free home value estimate so you at least know what it's worth? Takes 2 min: value.thejorgeramirezgroup.com"

---

### Sub-Flow 4D: General Inquiry

**1. Send Immediate Reply**
```
"Hey [First Name]! Got your message. What can I help you with?"
```

**2. Wait for Reply**

**3. Notify Jorge**
```
Slack/SMS:
"New message from [First Name]: '[Message]'"
```

---

## 🔄 WORKFLOW 5: Facebook Pixel Sync (Custom Audiences)

**Purpose**: Send GHL contact data back to Facebook for retargeting  
**Trigger**: Contact achieves milestone (downloaded guide, viewed listing, etc.)  
**Goal**: Enable Facebook Custom Audiences based on GHL activity

### Setup:

**Step 1: Install Facebook Conversions API in GHL**

GHL → Settings → Integrations → Facebook Conversions API

Connect your Facebook Business Account

**Step 2: Create Workflow**

**Automation → Create New → "Facebook Pixel Event Sender"**

#### Trigger Options (create separate workflows for each):

**Trigger A**: Tag Added: "Downloaded Seller Guide"  
**Trigger B**: Tag Added: "Viewed Listing: [Address]"  
**Trigger C**: Tag Added: "Hot Seller Lead"  
**Trigger D**: Tag Added: "Booked Showing"

#### Actions:

**1. Send Custom Event to Facebook Pixel**

GHL → Webhook → POST to Facebook Conversions API

```json
{
  "data": [
    {
      "event_name": "SellerGuideDownload", // or "ListingView", "HotLead", etc.
      "event_time": "[Unix Timestamp]",
      "user_data": {
        "em": "[Email - hashed SHA256]",
        "ph": "[Phone - hashed SHA256]",
        "fn": "[First Name - hashed]",
        "ln": "[Last Name - hashed]"
      },
      "custom_data": {
        "content_name": "Seller Guide",
        "content_category": "Lead Magnet",
        "value": 100.00,
        "currency": "USD"
      }
    }
  ]
}
```

**2. Add Tag**
```
Tag: "FB Pixel: [Event Name]"
```

**3. Update Custom Field**
```
Field: "Last FB Pixel Event"
Value: [Event Name] at [Timestamp]
```

---

### Step 3: Create Facebook Custom Audiences

Now that GHL is sending events to Facebook, create Custom Audiences:

**Facebook Ads Manager → Audiences → Create Custom Audience → Website**

**Audience 1: Seller Guide Downloads (Last 30 Days)**
```
Event: SellerGuideDownload
Time window: Last 30 days
Exclude: Anyone who submitted contact form (they're already in pipeline)
```

**Audience 2: Listing Viewers (Last 7 Days)**
```
Event: ListingView
Time window: Last 7 days
Exclude: Anyone who booked showing
```

**Audience 3: Hot Seller Leads (Last 60 Days)**
```
Event: HotLead
Time window: Last 60 days
Include: High-value prospects
```

---

## 📊 WORKFLOW 6 (BONUS): Lead Scoring Automation

**Purpose**: Automatically score leads based on behavior  
**Trigger**: Any activity (email open, page view, message sent)  
**Goal**: Prioritize hot leads for Jorge's attention

### Setup:

**Automation → Create New → "Lead Score Calculator"**

#### Scoring Rules:

**+10 points**: Downloaded Seller Guide  
**+15 points**: Viewed "How We Sell" page  
**+20 points**: Viewed specific listing  
**+25 points**: Replied to SMS/email  
**+30 points**: Requested showing  
**+50 points**: Submitted contact form  
**+100 points**: Booked appointment on calendar  

**-5 points per week**: No activity (decay over time)

#### Actions Based on Score:

**Score 0-25**: Cold Lead
- Tag: "Temperature: Cold"
- Nurture: Email drip campaign (monthly)

**Score 26-75**: Warm Lead
- Tag: "Temperature: Warm"
- Nurture: SMS + email (weekly)

**Score 76-150**: Hot Lead
- Tag: "Temperature: Hot"
- Action: Notify Jorge immediately
- Nurture: Daily SMS follow-up

**Score 151+**: Red Hot Lead
- Tag: "Temperature: 🔥 RED HOT"
- Action: Call Jorge's cell immediately
- Nurture: Personal call + text within 1 hour

---

## 🔧 TECHNICAL SETUP CHECKLIST

**Before building workflows:**

- [ ] Facebook Pixel installed on all pages
- [ ] Facebook Conversions API connected in GHL
- [ ] UTM parameters added to all Facebook ads
- [ ] Webhook endpoints created in GHL
- [ ] Custom fields created: Lead Source, Campaign, Ad Name, Listing Viewed, Lead Score
- [ ] Tags created: All campaigns, ad types, temperature levels
- [ ] Forms embedded: Seller Guide download, Contact, Showing Request
- [ ] Calendar integrated: Google Calendar (jorge.ramirez@kw.com)
- [ ] SMS/Email templates written (use templates from Facebook ad doc)
- [ ] Slack/SMS notifications configured for Jorge

---

## 📈 TESTING WORKFLOW

**Test each workflow before going live:**

1. **Submit test form** (use your own email)
2. **Check workflow triggered** (GHL → Automation → History)
3. **Verify tags added** (Contacts → Search your test contact)
4. **Confirm emails sent** (Check inbox)
5. **Check Facebook pixel fired** (Facebook Events Manager → Test Events)
6. **Validate Custom Audience** (Facebook Ads Manager → Audiences → Check size)

**Test Facebook ad flow end-to-end:**

1. Create test ad (targeting only you)
2. Click ad on mobile
3. Land on page with UTM parameters
4. Submit form
5. Check GHL: Did workflow trigger?
6. Check Facebook: Did pixel fire?
7. Check email: Did auto-response arrive?
8. Check SMS: Did follow-up send?

---

## 🚨 TROUBLESHOOTING

**Workflow didn't trigger:**
- Check trigger conditions (is tag spelled correctly?)
- Verify contact exists in GHL
- Check workflow status (is it active/published?)

**Facebook pixel not firing:**
- Use Facebook Pixel Helper Chrome extension
- Check console for JavaScript errors
- Verify Pixel ID matches Business Manager

**Custom Audience size = 0:**
- Takes 24-48 hours to populate
- Need minimum 100 people
- Check event names match exactly

**SMS not sending:**
- Verify phone number format (+1XXXXXXXXXX)
- Check A2P 10DLC approval status
- Confirm SMS enabled in GHL Settings

---

## 💡 OPTIMIZATION TIPS

**Week 1-2: Monitor & Adjust**
- Watch which workflows trigger most
- Check response rates (% of people replying)
- Pause underperforming flows

**Week 3-4: Scale What Works**
- Duplicate winning workflows
- Test new message variations
- Increase Facebook ad budgets on best performers

**Monthly: Review & Refine**
- Check lead scores (are hot leads really hot?)
- Update Custom Audiences (exclude converters)
- Refresh ad creative (avoid fatigue)
- Audit UTM tracking (any broken links?)

---

## 📊 KEY METRICS TO TRACK

**In GHL:**
- Workflow trigger rate (how many fire per day?)
- Conversion rate (workflow trigger → booked appointment)
- Lead score distribution (cold vs. warm vs. hot)
- Response time (contact arrives → Jorge replies)

**In Facebook:**
- Custom Audience size (growing over time?)
- Retargeting ad CTR (click-through rate)
- Cost per lead (Facebook spend ÷ leads generated)
- ROAS (Return on Ad Spend)

**Your Goal Benchmarks:**
- Response time: <1 hour (ideally <15 min)
- Workflow→Appointment rate: 10-15%
- Facebook CTR: 2-5% (retargeting)
- Cost per seller lead: <$50

---

**Questions? Need help implementing?**  
These workflows are the engine that makes your Facebook ads actually work.

*Last updated: February 3, 2026*
