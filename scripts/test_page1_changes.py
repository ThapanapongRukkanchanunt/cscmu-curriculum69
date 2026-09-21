import asyncio
from playwright.async_api import async_playwright

async def test_page1():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1280, 'height': 1400})
        await page.goto('file:///D:/Documents/curriculum69/index.html')
        await page.wait_for_timeout(600)
        
        # Check total credits
        total_cr = await page.inner_text('#stat-total-credits')
        ge_cr = await page.inner_text('#stat-ge-credits')
        print(f'Co-op Total: {total_cr} cr | GE: {ge_cr} cr')
        
        # Click Project plan
        proj_btn = await page.query_selector('.plan-toggle-btn[data-plan="project"]')
        await proj_btn.click()
        await page.wait_for_timeout(300)
        proj_total_cr = await page.inner_text('#stat-total-credits')
        print(f'Project-oriented Total: {proj_total_cr} cr')
        
        # Check category tables rendered
        sec_count = len(await page.query_selector_all('#category-tables-container .section-block'))
        print(f'Category tables rendered: {sec_count}')
        
        # Check course links in category tables
        course_links = len(await page.query_selector_all('#category-tables-container a'))
        print(f'Course links in tables: {course_links}')
        
        # Capture updated screenshot
        await page.screenshot(path='C:/Users/CS-DELL-7470/.gemini/antigravity/brain/2c2f7d6f-4672-4cd3-9891-47ad092dad93/overview_categories_desktop.png')
        print('Screenshot saved to overview_categories_desktop.png')
        
        await browser.close()

asyncio.run(test_page1())
