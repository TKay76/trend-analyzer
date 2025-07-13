### **[Work Order] Trend Analysis Database Construction & Scraper Integration (MVP v1)**

* **Project Name:** Short-form Music Trend Analysis Service
* **Task:** Data Pipeline Construction - Phase 1 (MVP)
* **Date:** July 13, 2025
* **Assigned To:** [Developer's Name]

---

#### **1. Overview**

The objective of this task is to build a central database to **permanently store the chart data collected by the PoC 2 and PoC 3 scrapers** (from TikTok and YouTube). This will allow us to systematically manage the data for AI analysis and establish the foundation for time-series trend analysis by accumulating historical data.

---

#### **2. Final Deliverable**

1.  **A PostgreSQL database schema**, including `songs` and `daily_trends` tables, capable of storing the trend data.
2.  **Modified versions of `tiktok_music_scraper.py` and `youtube_music_scraper.py`** that save their collected data directly into the newly created PostgreSQL database instead of printing to the console.

---

#### **3. Key Functional Specifications**

**3.1. Database Schema Design**

* **Database Name:** `trend_analysis`
* **Table 1: `songs` (Master Song Information)**
    * **Columns:**
        * `id`: `SERIAL PRIMARY KEY` (Unique identifier)
        * `title`: `VARCHAR(255)` (Track title)
        * `artist`: `VARCHAR(255)` (Artist name)
        * `thumbnail_url`: `TEXT` (Thumbnail image URL, from YouTube)
        * `is_approved_for_business_use`: `BOOLEAN` (Is it approved for business use on TikTok?)
        * `created_at`: `TIMESTAMP` (First time the song was saved)
    * **Constraint:** The combination of `title` and `artist` must be unique (`UNIQUE` constraint).

* **Table 2: `daily_trends` (Daily Trend Data)**
    * **Columns:**
        * `id`: `SERIAL PRIMARY KEY` (Unique identifier)
        * `song_id`: `INTEGER` (Foreign Key referencing `songs.id`)
        * `source`: `VARCHAR(50)` (Data source: 'tiktok', 'youtube')
        * `category`: `VARCHAR(50)` (Category: 'popular', 'breakout', 'trending', etc.)
        * `rank`: `INTEGER` (The rank for that day)
        * `metrics`: `JSONB` (Other metrics: view counts, changes, etc.)
        * `date`: `DATE` (The date the data was collected)

**3.2. Scraper Integration Logic**

* **DB Connection:** Each script must connect to the local PostgreSQL database (`localhost`) at the beginning of its execution and close the connection upon completion.
* **Data Storage Process (Upsert Logic):**
    1.  When the scraper collects song information, it first checks if the song already exists in the `songs` table based on `title` and `artist`.
    2.  **If the song does not exist (New Song):** It will `INSERT` the new song information into the `songs` table and retrieve the newly generated `song_id`.
    3.  **If the song already exists:** It will retrieve the existing `song_id`.
    4.  Using the retrieved `song_id`, it will `INSERT` the collected rank, source, category, and date information as a new row in the `daily_trends` table.

---

#### **4. Tech Stack & Environment**

* **Database:** PostgreSQL (local installation)
* **Language:** Python 3.9+
* **Core Libraries:**
    * `psycopg2-binary`: PostgreSQL adapter for Python
    * Existing scraper libraries (`playwright`, `beautifulsoup4`)

---

#### **5. Success Criteria**

* When `tiktok_music_scraper.py` and `youtube_music_scraper.py` are executed, do they run without errors and accurately save the data to the `songs` and `daily_trends` tables in PostgreSQL?
* When the same song is scraped multiple times, is it saved only once in the `songs` table, while its daily rank data is correctly accumulated in the `daily_trends` table?

---

#### **Developer Feedback Request**

* Please feel free to propose any improvements to the database schema or storage logic for better efficiency or scalability. Ideas considering performance with large datasets are especially welcome.