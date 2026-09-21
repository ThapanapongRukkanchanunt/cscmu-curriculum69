import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Test at standard desktop 1280x850 and 1440x900
        for width, height in [(1280, 850), (1440, 900)]:
            page = await browser.new_page(viewport={"width": width, "height": height})
            url = f"file:///{os.path.abspath('map.html').replace(os.sep, '/')}"
            print(f"Loading {url} at {width}x{height}...")
            await page.goto(url)
            await page.wait_for_timeout(1000)

            # Check horizontal overflow
            scroll_info = await page.evaluate('''() => {
                const wrapper = document.querySelector('.curriculum-map-wrapper');
                const grid = document.querySelector('.curriculum-map-grid');
                return {
                    docScroll: document.documentElement.scrollWidth,
                    docClient: document.documentElement.clientWidth,
                    hasDocHScroll: document.documentElement.scrollWidth > document.documentElement.clientWidth,
                    wrapperScroll: wrapper ? wrapper.scrollWidth : 0,
                    wrapperClient: wrapper ? wrapper.clientWidth : 0,
                    hasWrapperHScroll: wrapper ? wrapper.scrollWidth > wrapper.clientWidth : false,
                    gridCols: grid ? window.getComputedStyle(grid).gridTemplateColumns.split(' ').length : 0
                };
            }''')
            print(f"[{width}px] Scroll info: {scroll_info}")

            # Check term pills logic
            term_pill_samples = await page.evaluate('''() => {
                const cards = Array.from(document.querySelectorAll('.map-course-card'));
                return cards.slice(0, 15).map(c => {
                    const cid = c.dataset.cid;
                    const pills = Array.from(c.querySelectorAll('.term-pill')).map(p => p.textContent.trim());
                    return { cid, pills };
                });
            }''')
            print(f"[{width}px] Sample term pills: {term_pill_samples[:5]}")

            # Hover on 204255 (OOP & Data Structures)
            card_to_hover = page.locator('.map-course-card[data-cid="204255"]').first
            if await card_to_hover.count() > 0:
                await card_to_hover.hover()
                await page.wait_for_timeout(500)
                
                # Check highlighted classes
                highlight_counts = await page.evaluate('''() => {
                    return {
                        active: document.querySelectorAll('.map-course-card.is-active').length,
                        prereq: document.querySelectorAll('.map-course-card.is-prereq').length,
                        postreq: document.querySelectorAll('.map-course-card.is-postreq').length,
                        dimmed: document.querySelectorAll('.map-course-card.is-dimmed').length
                    };
                }''')
                print(f"[{width}px] Hover highlight counts on 204255: {highlight_counts}")

            screenshot_path = f"C:/Users/CS-DELL-7470/.gemini/antigravity/brain/2c2f7d6f-4672-4cd3-9891-47ad092dad93/map_{width}_hover.png"
            await page.screenshot(path=screenshot_path)
            print(f"Saved screenshot: {screenshot_path}")

        # Also test dark mode
        dark_page = await browser.new_page(viewport={"width": 1366, "height": 850})
        await dark_page.goto(f"file:///{os.path.abspath('map.html').replace(os.sep, '/')}")
        await dark_page.click('#theme-toggle-btn')
        await dark_page.wait_for_timeout(400)
        card_to_hover = dark_page.locator('.map-course-card[data-cid="204255"]').first
        if await card_to_hover.count() > 0:
            await card_to_hover.hover()
            await dark_page.wait_for_timeout(500)
        dark_screenshot_path = "C:/Users/CS-DELL-7470/.gemini/antigravity/brain/2c2f7d6f-4672-4cd3-9891-47ad092dad93/map_dark_hover.png"
        await dark_page.screenshot(path=dark_screenshot_path)
        print(f"Saved dark screenshot: {dark_screenshot_path}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
