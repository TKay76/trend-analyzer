[Work Order] PoC Script Development for TikTok Sound Data Scraping

- **Project Name:** Short-form Music Trend Analysis Service
- **Task:** Proof of Concept (PoC) for Core Technology
- **Date:** July 12, 2025
- **Assigned To:** [Developer's Name]

---

### **1. Overview**

The objective of this task is to verify the technical feasibility of scraping sound data from the TikTok platform, which is the core technology for our "Short-form Music Trend Analysis Service." The goal is to validate the riskiest part of the project—the data scraping mechanism—with minimal resources before building the full system.

### **2. Final Deliverable**

- **A single Python script (`scraper_poc.py`) that accepts one TikTok 'Sound' page URL as input, extracts the 'total video count' for that sound, and prints the result to the console as an integer.**

### **3. Key Functional Specifications**

1. **Input:**
    - The script must accept a single, full TikTok 'Sound' page URL as a command-line argument upon execution.
    - *Example:* `python scraper_poc.py "https://www.tiktok.com/music/original-sound-73886-orijinal-ses-7388654812869528322"`
2. **Process:**
    - **Browser Automation:** Use `Selenium` or `Playwright` to launch and control a real web browser (e.g., Chrome) in a headless or foreground state.
    - **Navigate to URL:** Navigate to the URL provided as input.
    - **Wait for Data to Load:** Since TikTok pages load content dynamically, the script must use an **Explicit Wait** mechanism to ensure the target data is present on the page before attempting to scrape it. (Avoid using fixed `time.sleep()` calls).
    - **Data Extraction:** Parse the page's HTML structure (using `BeautifulSoup` or `Parsel`) to locate the element containing the 'total video count' and extract its text content.
        - *Note:* As of 2025-07-12, this information may be found within `h2` or `strong` tags, associated with text like "videos". This structure is subject to change.
    - **Data Parsing:** Clean the extracted text (e.g., "1.4M videos", "1,400,000 videos") by removing all non-numeric characters (commas, letters). Accurately convert suffixes like 'K' (for thousands) and 'M' (for millions) into their full integer equivalents (e.g., '1.4M' becomes `1400000`).
3. **Output:**
    - Print the final, parsed integer representing the total video count to the console.
    - *Success Output Example:* `1400000`
    - *Failure Output Example:* An error message or `0`.

### **4. Tech Stack & Environment**

- **Language:** Python 3.9+
- **Core Libraries:**
    - `selenium` or `playwright` (for browser automation)
    - `beautifulsoup4` or `parsel` (for HTML parsing)
- **Development Environment:** Develop and test in a local PC environment.

### **5. Success Criteria**

**This PoC will be considered successful if and only if all three of the following criteria are met:**

1. Does the script execute from start to finish without errors, accepting a URL as a command-line argument without requiring manual intervention or code changes?
2. Does the script function correctly when tested with at least three different, valid TikTok sound URLs?
3. Does the script's final output number precisely match the 'total video count' observed visually on the live webpage (including correct conversion of 'K'/'M' suffixes)?

### **6. Anticipated Obstacles & Considerations**

- **HTML Structure Changes:** TikTok frequently updates its website structure. The scraper should be designed to be as resilient as possible, perhaps by relying on relative element positioning rather than brittle selectors like specific class names.
- **Anti-Scraping Measures:** While unlikely to be a major issue for a small-scale PoC, be aware that future development will need to handle challenges like CAPTCHAs and IP-based blocking.
- **Dynamic Loading:** This is the most common point of failure. The script's logic for waiting for elements to load must be robust.

---

### **Developer Feedback & Suggestions**

Your expertise is highly valued. If you believe there is a more efficient, robust, or scalable approach to achieve this PoC's goal, please do not hesitate to propose your suggestions. We are open to discussing alternative methods before proceeding with development.