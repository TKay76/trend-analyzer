### **[Work Order] PoC for TikTok Creative Center Music Trend Data Scraping**

  * **Project Name:** Short-form Music Trend Analysis Service
  * **Task:** Core Technology Proof of Concept (PoC) - v2
  * **Date:** July 12, 2025
  * **Assigned To:** [Developer's Name]

-----

#### **1. Overview**

The objective of this task is to technically verify our ability to successfully extract data from the **'Popular Music' page within the official TikTok Creative Center**. The success of this PoC is a critical milestone, proving the feasibility of acquiring the project's core data.

-----

#### **2. Final Deliverable**

  * **A single Python script that navigates to the specified TikTok Creative Center popular music page, scrapes the music ranking lists from both the 'Popular' and 'Breakout' tabs, and extracts the 'Rank, Track Title, and Artist Name' for each track, printing the structured result to the console.**

-----

#### **3. Key Functional Specifications**

1.  **Initial Navigation:**

      * The script shall navigate to the hardcoded URL: `https://ads.tiktok.com/business/creativecenter/inspiration/popular/music/pc/en`.
      * **Login Handling:** If login is required, the script must include a login sequence. (Credentials should be managed via a separate configuration file).

2.  **Scrape 'Popular' Tab Data:**

      * After the page loads, scrape the data from the default 'Popular' tab.
      * **Scope:** The entire visible list of songs (typically Top 100).
      * **Fields to Extract:**
          * `Rank` (integer)
          * `Track` (string, contains title and artist)
      * It is recommended to parse the 'Track' data to separate it into **'Title' and 'Artist'**.

3.  **Switch to and Scrape 'Breakout' Tab Data:**

      * After completing the 'Popular' tab scrape, **programmatically click the "Breakout" tab button**.
      * Implement an **explicit wait** for the page content to dynamically update and the 'Breakout' tab's data to fully load.
      * Scrape the entire list from the 'Breakout' tab for the same `Rank` and `Track` fields.

4.  **Structured Output:**

      * Display all collected data on the console, clearly distinguished by 'Popular' and 'Breakout' sections, preferably in a JSON format for readability.
      * **Example Output:**
        ```json
        {
          "popular": [
            {"rank": 1, "title": "Espresso", "artist": "Sabrina Carpenter"},
            {"rank": 2, "title": "A Bar Song (Tipsy)", "artist": "Shaboozey"},
            ...
          ],
          "breakout": [
            {"rank": 1, "title": "BIRDS OF A FEATHER", "artist": "Billie Eilish"},
            {"rank": 2, "title": "Good Luck, Babe!", "artist": "Chappell Roan"},
            ...
          ]
        }
        ```

-----

#### **4. Tech Stack & Environment**

  * **Language:** Python 3.9+
  * **Core Libraries:**
      * **`selenium` or `playwright`:** For dynamic web page control and automation.
      * **`beautifulsoup4` or `parsel`:** For HTML structure analysis and data parsing.

-----

#### **5. Success Criteria**

  * Does the script run and successfully fetch data from both the 'Popular' and 'Breakout' tabs without manual intervention?
  * Does the extracted data (rank, title, artist) accurately match the content on the live website?
  * Is the final output structured correctly as specified in the 'Structured Output' example?

-----

#### **6. Anticipated Obstacles & Key Challenges**

  * **Login Wall:** If login is mandatory, a robust, automated login sequence must be implemented. Potential anti-bot mechanisms like CAPTCHA will need a defined solution.
  * **Dynamic Loading Waits:** Stably detecting content changes after a tab click and waiting appropriately is critical. Incorrect timing is a primary cause of data omission.
  * **HTML Structure Analysis:** A thorough initial analysis using browser Developer Tools (F12) to precisely identify the HTML tags and class names of target data is a prerequisite.

-----

#### **Developer Feedback Request**

After reviewing this work order, please do not hesitate to propose a more efficient or robust technical approach. For instance, if you see an opportunity to find a hidden API request instead of relying on browser automation, we are eager to discuss better alternatives.