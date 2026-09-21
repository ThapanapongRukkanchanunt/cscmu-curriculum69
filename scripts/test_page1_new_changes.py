import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1366, "height": 900})
        url = f"file:///{os.path.abspath('index.html').replace(os.sep, '/')}"
        print(f"Loading {url}...")
        await page.goto(url)
        await page.wait_for_timeout(800)

        # 1. Verify Major Electives have NO 100 or 200 level courses
        electives_info = await page.evaluate('''() => {
            const projSec = document.querySelector('#section-major_electives_proj');
            const nonProjSec = document.querySelector('#section-major_electives_nonproj');
            
            const getCourseIds = (sec) => {
                if (!sec) return [];
                return Array.from(sec.querySelectorAll('tbody tr td:first-child')).map(td => td.textContent.trim());
            };
            
            const projIds = getCourseIds(projSec);
            const nonProjIds = getCourseIds(nonProjSec);
            
            const invalidProj = projIds.filter(id => parseInt(id.slice(3, 4), 10) < 3);
            const invalidNonProj = nonProjIds.filter(id => parseInt(id.slice(3, 4), 10) < 3);
            
            return {
                projCount: projIds.length,
                nonProjCount: nonProjIds.length,
                invalidProj,
                invalidNonProj,
                sampleProj: projIds.slice(0, 5),
                sampleNonProj: nonProjIds.slice(0, 5)
            };
        }''')
        print(f"Electives check: {electives_info}")
        assert len(electives_info['invalidProj']) == 0, f"Found 100/200 level courses in proj: {electives_info['invalidProj']}"
        assert len(electives_info['invalidNonProj']) == 0, f"Found 100/200 level courses in non-proj: {electives_info['invalidNonProj']}"

        # 2. Verify Term Badges
        term_badge_classes = await page.evaluate('''() => {
            const pills = Array.from(document.querySelectorAll('.term-pill'));
            const classes = new Set();
            pills.forEach(p => classes.add(p.className));
            return Array.from(classes);
        }''')
        print(f"Term pill classes found: {term_badge_classes}")
        assert any('t1-pill' in c for c in term_badge_classes) or any('t2-pill' in c for c in term_badge_classes), "No t1-pill or t2-pill found!"

        # Scroll to GE section
        gened_elem = page.locator('#section-gened')
        await gened_elem.scroll_into_view_if_needed()
        await page.wait_for_timeout(400)

        # Screenshot default state (< B1)
        await page.screenshot(path="C:/Users/CS-DELL-7470/.gemini/antigravity/brain/2c2f7d6f-4672-4cd3-9891-47ad092dad93/overview_ge_below_b1.png", full_page=False)

        # 3. Click B1+ button
        b1_btn = page.locator('.ge-lang-btn:has-text("B1+")').first
        await b1_btn.click()
        await page.wait_for_timeout(500)

        # Verify B1+ content
        b1_check = await page.evaluate('''() => {
            const genedSec = document.querySelector('#section-gened');
            const details = Array.from(genedSec.querySelectorAll('details.ge-expandable-card'));
            const summaryTexts = details.map(d => d.querySelector('summary').textContent.trim());
            const rowsInFirstDetails = details[0] ? Array.from(details[0].querySelectorAll('tbody tr td:first-child')).map(td => td.textContent.trim()) : [];
            return {
                detailsCount: details.length,
                summaryTexts,
                rowsInFirstDetails
            };
        }''')
        print(f"B1+ details count: {b1_check['detailsCount']}, first details rows: {b1_check['rowsInFirstDetails']}")
        assert "001201" in b1_check['rowsInFirstDetails'], "001201 not found in B1+ electives!"

        # Open creativity expandable to check options
        creativity_summary = page.locator('details.ge-expandable-card summary:has-text("คิดสร้างสรรค์")').first
        if await creativity_summary.count() > 0:
            await creativity_summary.click()
            await page.wait_for_timeout(300)

        # Re-scroll to language toolbar
        toolbar = page.locator('.ge-lang-toolbar')
        await toolbar.scroll_into_view_if_needed()
        await page.wait_for_timeout(300)

        # Screenshot B1+ state with expanded details
        screenshot_path = "C:/Users/CS-DELL-7470/.gemini/antigravity/brain/2c2f7d6f-4672-4cd3-9891-47ad092dad93/overview_ge_b1plus_focused.png"
        await page.screenshot(path=screenshot_path, full_page=False)
        print(f"Saved screenshot: {screenshot_path}")

        await browser.close()
        print("All Page 1 verification assertions passed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
