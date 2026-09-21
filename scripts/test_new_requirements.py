import asyncio
from playwright.async_api import async_playwright
import os
import sys

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = r"C:\Users\CS-DELL-7470\.gemini\antigravity\brain\2c2f7d6f-4672-4cd3-9891-47ad092dad93"
BASE_DIR = r"D:\Documents\curriculum69"

async def test_page2_english_score_toggle(page):
    print("\n--- Testing Page 2: English Score Toggle ---")
    url = f"file:///{BASE_DIR.replace(os.sep, '/')}/map.html"
    await page.goto(url)
    await page.wait_for_selector(".map-course-card")

    # 1. Default (< B1)
    card_1101 = await page.query_selector('.map-column[data-sem="Y1S1"] .map-course-card[data-cid="001101"]')
    card_1102 = await page.query_selector('.map-column[data-sem="Y1S2"] .map-course-card[data-cid="001102"]')
    card_1225 = await page.query_selector('.map-column[data-sem="Y2S1"] .map-course-card[data-cid="001225"]')

    assert card_1101 is not None, "Course 001101 should be in Y1S1 for < B1"
    assert card_1102 is not None, "Course 001102 should be in Y1S2 for < B1"
    assert card_1225 is not None, "Course 001225 should be in Y2S1 for < B1"
    print("Default (< B1) verified: 001101 in Y1S1, 001102 in Y1S2, 001225 in Y2S1.")

    await page.screenshot(path=os.path.join(ARTIFACT_DIR, "page2_map_below_b1.png"))

    # 2. Toggle to B1+
    b1_plus_btn = await page.query_selector('.map-lang-score-btn[data-score="b1_plus"]')
    assert b1_plus_btn is not None, "B1+ button not found on Page 2!"
    await b1_plus_btn.click()
    await page.wait_for_timeout(200)

    card_1225_y1s1 = await page.query_selector('.map-column[data-sem="Y1S1"] .map-course-card[data-cid="001225"]')
    card_ge_engl_y1s2 = await page.query_selector('.map-column[data-sem="Y1S2"] .map-course-card[data-cid="GE_ENGL_1"]')
    card_ge_engl_y2s1 = await page.query_selector('.map-column[data-sem="Y2S1"] .map-course-card[data-cid="GE_ENGL_2"]')

    assert card_1225_y1s1 is not None, "Course 001225 should be in Y1S1 for B1+"
    assert card_ge_engl_y1s2 is not None, "English Elective should be in Y1S2 for B1+"
    assert card_ge_engl_y2s1 is not None, "English Elective should be in Y2S1 for B1+"
    print("B1+ verified: 001225 in Y1S1, English Elective in Y1S2, English Elective in Y2S1.")

    await page.screenshot(path=os.path.join(ARTIFACT_DIR, "page2_map_b1_plus.png"))

    # 3. Toggle back to < B1
    below_b1_btn = await page.query_selector('.map-lang-score-btn[data-score="below_b1"]')
    await below_b1_btn.click()
    await page.wait_for_timeout(200)

    card_1101_again = await page.query_selector('.map-column[data-sem="Y1S1"] .map-course-card[data-cid="001101"]')
    assert card_1101_again is not None, "Course 001101 should return to Y1S1 when switching back to < B1"
    print("Reverted to < B1 successfully.")

async def test_page3_drawer_removed_mini_graph(page):
    print("\n--- Testing Page 3: Removal of Dependency Mini Graph from Drawer ---")
    url = f"file:///{BASE_DIR.replace(os.sep, '/')}/tree.html"
    await page.goto(url)
    await page.wait_for_selector(".list-course-card")

    # Click on a course
    first_card = await page.query_selector(".list-course-card")
    await first_card.click()
    await page.wait_for_selector("#course-drawer.open")
    await page.wait_for_timeout(200)

    # Assert that #drawer-mini-graph does NOT exist
    mini_graph = await page.query_selector("#drawer-mini-graph")
    assert mini_graph is None, "Dependency mini graph was NOT removed from drawer!"
    print("Verified: #drawer-mini-graph is completely removed.")

    # Assert that official prereq section and postreq section exist and are clean
    prereq_str = await page.query_selector("#drawer-prereq-str")
    assert prereq_str is not None, "Official prerequisite section missing!"
    prereq_tags = await page.query_selector("#drawer-prereqs-tags")
    assert prereq_tags is not None, "Prerequisites tags missing!"
    postreq_tags = await page.query_selector("#drawer-postreqs-tags")
    assert postreq_tags is not None, "Postrequisites tags missing!"

    print("Verified: Prerequisite & Postrequisite sections are intact without redundancy.")
    await page.screenshot(path=os.path.join(ARTIFACT_DIR, "page3_drawer_clean_no_mini_graph.png"))

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        await test_page2_english_score_toggle(page)
        await test_page3_drawer_removed_mini_graph(page)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
