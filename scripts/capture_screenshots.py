import asyncio
from playwright.async_api import async_playwright

async def take_screenshots():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        # 1. Desktop Overview
        page = await browser.new_page(viewport={'width': 1280, 'height': 900})
        await page.goto('http://localhost:8088/index.html')
        await page.wait_for_timeout(1000)
        await page.screenshot(path='C:/Users/CS-DELL-7470/.gemini/antigravity/brain/2c2f7d6f-4672-4cd3-9891-47ad092dad93/overview_desktop.png')
        
        # 1b. Mobile Overview
        m_page = await browser.new_page(viewport={'width': 390, 'height': 844})
        await m_page.goto('http://localhost:8088/index.html')
        await m_page.wait_for_timeout(1000)
        await m_page.screenshot(path='C:/Users/CS-DELL-7470/.gemini/antigravity/brain/2c2f7d6f-4672-4cd3-9891-47ad092dad93/overview_mobile.png')

        # 2. Desktop Map
        await page.goto('http://localhost:8088/map.html')
        await page.wait_for_timeout(1000)
        # Hover over 204212 or 204361 to show dependency highlight
        card = await page.query_selector('.map-course-card[data-cid="204212"]')
        if card:
            await card.hover()
            await page.wait_for_timeout(500)
        await page.screenshot(path='C:/Users/CS-DELL-7470/.gemini/antigravity/brain/2c2f7d6f-4672-4cd3-9891-47ad092dad93/map_desktop_hover.png')

        # 2b. Mobile Map
        await m_page.goto('http://localhost:8088/map.html')
        await m_page.wait_for_timeout(1000)
        await m_page.screenshot(path='C:/Users/CS-DELL-7470/.gemini/antigravity/brain/2c2f7d6f-4672-4cd3-9891-47ad092dad93/map_mobile.png')

        # 3. Desktop Tree (with drawer opened)
        await page.goto('http://localhost:8088/tree.html')
        await page.wait_for_timeout(1500)
        # Click a course card
        node = await page.query_selector('.tree-node-card[data-cid="204312"]')
        if node:
            await node.click()
            await page.wait_for_timeout(500)
        await page.screenshot(path='C:/Users/CS-DELL-7470/.gemini/antigravity/brain/2c2f7d6f-4672-4cd3-9891-47ad092dad93/tree_desktop_drawer.png')

        # 3b. Mobile Tree (List view)
        await m_page.goto('http://localhost:8088/tree.html')
        await m_page.wait_for_timeout(1000)
        await m_page.screenshot(path='C:/Users/CS-DELL-7470/.gemini/antigravity/brain/2c2f7d6f-4672-4cd3-9891-47ad092dad93/tree_mobile_list.png')

        await browser.close()
        print("Screenshots taken successfully!")

asyncio.run(take_screenshots())
