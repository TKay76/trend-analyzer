### **[Work Order] PoC for YouTube Music Shorts Popular Songs Data Scraping**

  * **Project Name:** Short-form Music Trend Analysis Service
  * **Task:** Core Technology Proof of Concept (PoC) - v3
  * **Date:** July 12, 2025
  * **Assigned To:** [Developer's Name]

-----

#### **1. Overview**

The objective of this task is to technically verify our ability to successfully extract data from the **'Daily Shorts Popular Songs'** section of the YouTube Music 'Charts & Insights' page. This PoC will confirm the possibility of expanding our data collection scope to include YouTube Shorts, a major platform, in addition to TikTok.

-----

#### **2. Final Deliverable**

  * A single Python script that navigates to the specified YouTube Music chart page, scrapes the music ranking lists from the three categories—**'Trending,' 'Top rising,' and 'Most popular new releases'**—and extracts the 'Rank, Title, Artist Name,' and other key information for each track, outputting the result in a structured JSON format.

-----

#### **3. Key Functional Specifications**

1.  **Initial Navigation:**

      * The script shall navigate to the specified URL (`https://charts.youtube.com/charts/TopShortsSongs/kr/daily`).
      * It is assumed this page does not require a login, but if it does, an automated login sequence must be implemented.

2.  **Data Scraping:**

      * Identify the **'Daily Shorts Popular Songs'** section on the page.
      * Scrape the data from each of the three sub-categories within this section: **'Trending,' 'Top rising,' and 'Most popular new releases.'**
      * **Fields to Extract (common to all categories):**
          * `Rank` (integer)
          * `Title` (string)
          * `Artist` (string)
          * `Thumbnail URL` (string)
          * `Daily Views / Change` (or any other meaningful metrics visible on the page, like daily view counts or rank changes).

3.  **Structured Output:**

      * Display all collected data on the console in a human-readable JSON format, clearly distinguished by the keys 'trending,' 'top\_rising,' and 'new\_releases.'
      * **Example Output:**
        ```json
        {
          "trending": [
            {"rank": 1, "title": "Song Title A", "artist": "Artist A", "thumbnail": "..."},
            {"rank": 2, "title": "Song Title B", "artist": "Artist B", "thumbnail": "..."},
            ...
          ],
          "top_rising": [
            {"rank": 1, "title": "Song Title C", "artist": "Artist C", "thumbnail": "..."},
            ...
          ],
          "new_releases": [
            {"rank": 1, "title": "Song Title D", "artist": "Artist D", "thumbnail": "..."},
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

  * Does the script successfully fetch data from all three categories: 'Trending,' 'Top rising,' and 'Most popular new releases'?
  * Does the extracted data (rank, title, artist, etc.) accurately match the content on the live website?
  * Is the final output structured correctly as specified in the 'Structured Output' example?

-----

#### **6. Anticipated Obstacles & Key Challenges**

  * **Content Identification:** The logic must accurately distinguish between the three different chart sections on a single page. Identifying the container elements for each section will be crucial.
  * **Data Loading:** The page might use 'Lazy Loading,' where data is only loaded as the user scrolls or clicks a button. The script may need scroll and wait logic to fetch the complete ranking data.
  * **Anti-Scraping:** Google/YouTube's anti-scraping policies can be sophisticated. Issues with running in `headless` mode should be anticipated, and the use of bypass techniques discussed in previous PoCs should be considered from the start.

-----

#### **Developer Feedback Request**

After reviewing this work order, please do not hesitate to propose a more efficient or robust technical approach. If you are aware of a better method specific to scraping YouTube Music data, we are eager to discuss it.