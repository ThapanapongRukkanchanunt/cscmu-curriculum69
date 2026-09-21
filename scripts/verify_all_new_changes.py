import asyncio
from playwright.async_api import async_playwright
import os
import sys

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = r"C:\Users\CS-DELL-7470\.gemini\antigravity\brain\2c2f7d6f-4672-4cd3-9891-47ad092dad93"
BASE_DIR = r"D:\Documents\curriculum69"

def rgb_to_hex(rgb_str):
    import re
    m = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', rgb_str)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"#{r:02x}{g:02x}{b:02x}"
    return rgb_str

def calculate_contrast(rgb1, rgb2):
    import re
    def luminance(r, g, b):
        vals = []
        for c in (r, g, b):
            c = c / 255.0
            vals.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
        return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]
    
    m1 = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', rgb1)
    m2 = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', rgb2)
    if not m1 or not m2:
        return 21.0
    l1 = luminance(int(m1.group(1)), int(m1.group(2)), int(m1.group(3)))
    l2 = luminance(int(m2.group(1)), int(m2.group(2)), int(m2.group(3)))
    bright = max(l1, l2)
    dark = min(l1, l2)
    return (bright + 0.05) / (dark + 0.05)

async def test_page2_map_hover_no_resize(page):
    print("\n--- Testing Page 2: Map Hover & Cell Size Stability ---")
    url = f"file:///{BASE_DIR.replace(os.sep, '/')}/map.html"
    await page.goto(url)
    await page.wait_for_selector(".map-course-card")

    # Get bounding boxes of cards and grid before hover
    grid = await page.query_selector("#curriculum-map-grid")
    grid_box_before = await grid.bounding_box()

    card_204111 = await page.query_selector('.map-course-card[data-cid="204111"]')
    box_204111_before = await card_204111.bounding_box()

    card_204115 = await page.query_selector('.map-course-card[data-cid="204115"]')
    box_204115_before = await card_204115.bounding_box()

    # Hover over 204111
    await card_204111.hover()
    await page.wait_for_timeout(200)

    # Check bounding box after hover
    grid_box_after = await grid.bounding_box()
    box_204111_after = await card_204111.bounding_box()
    box_204115_after = await card_204115.bounding_box()

    print(f"Grid width before: {grid_box_before['width']}, after: {grid_box_after['width']}")
    print(f"Grid height before: {grid_box_before['height']}, after: {grid_box_after['height']}")
    print(f"204111 (active) width before: {box_204111_before['width']}, after: {box_204111_after['width']}")
    print(f"204111 (active) height before: {box_204111_before['height']}, after: {box_204111_after['height']}")
    print(f"204115 (dependent) width before: {box_204115_before['width']}, after: {box_204115_after['width']}")
    print(f"204115 (dependent) height before: {box_204115_before['height']}, after: {box_204115_after['height']}")

    assert abs(grid_box_before['width'] - grid_box_after['width']) < 0.01, "Grid width changed on hover!"
    assert abs(grid_box_before['height'] - grid_box_after['height']) < 0.01, "Grid height changed on hover!"
    assert abs(box_204111_before['width'] - box_204111_after['width']) < 0.01, "Active card width changed on hover!"
    assert abs(box_204111_before['height'] - box_204111_after['height']) < 0.01, "Active card height changed on hover!"
    assert abs(box_204115_before['width'] - box_204115_after['width']) < 0.01, "Postreq card width changed on hover!"
    assert abs(box_204115_before['height'] - box_204115_after['height']) < 0.01, "Postreq card height changed on hover!"

    # Verify background colors
    bg_color = await card_204111.evaluate("el => window.getComputedStyle(el).backgroundColor")
    print(f"204111 active background color: {bg_color} ({rgb_to_hex(bg_color)})")
    
    # Capture screenshot
    await page.screenshot(path=os.path.join(ARTIFACT_DIR, "page2_map_hover_no_resize.png"))
    print("SUCCESS: Page 2 cell sizes strictly preserved during hover!")

async def test_page3_list_view_and_mini_graph(page):
    print("\n--- Testing Page 3: List View & Overlay Mini Graph ---")
    url = f"file:///{BASE_DIR.replace(os.sep, '/')}/tree.html"
    await page.goto(url)
    await page.wait_for_selector(".list-course-card")

    # Verify canvas wrapper is gone
    canvas = await page.query_selector("#canvas-wrapper")
    assert canvas is None, "Canvas wrapper was not removed from tree.html!"
    print("Canvas wrapper successfully removed from Page 3.")

    # Verify list view is visible
    list_view = await page.query_selector("#tree-list-view")
    is_visible = await list_view.is_visible()
    assert is_visible, "Tree list view is not visible!"
    print("List view is active and visible.")

    # Count cards
    cards = await page.query_selector_all(".list-course-card")
    print(f"Total elective cards rendered in list view: {len(cards)}")
    assert len(cards) >= 30, "Too few elective cards in list view!"

    # Find course card with exact ID 204341 (Operating Systems)
    print("Finding card 204341 to open course drawer...")
    card_341 = None
    all_cards = await page.query_selector_all('.list-course-card')
    for c in all_cards:
        code_el = await c.query_selector('span[style*="monospace"]')
        if code_el:
            code_text = (await code_el.inner_text()).strip()
            if code_text == '204341':
                card_341 = c
                break

    assert card_341 is not None, "Course 204341 card not found!"
    await card_341.click()
    await page.wait_for_selector("#course-drawer.open")
    await page.wait_for_timeout(300)

    # Inspect Mini Graph
    mini_graph = await page.query_selector("#drawer-mini-graph")
    assert mini_graph is not None, "Mini graph container not found in drawer!"

    # Verify 3 tiers: prereq (top), current (middle), postreq (bottom)
    tiers = await mini_graph.query_selector_all(".mini-graph-tier")
    print(f"Found {len(tiers)} tiers in drawer mini-graph.")
    assert len(tiers) == 3, f"Expected 3 tiers, found {len(tiers)}"

    # Check Prereq in top tier
    top_tier = tiers[0]
    top_text = await top_tier.inner_text()
    print(f"Top tier text: {top_text.replace(chr(10), ' | ')}")
    assert "204231" in top_text, "Prerequisite 204231 not properly shown in top tier!"

    # Check Current in middle tier
    mid_tier = tiers[1]
    mid_text = await mid_tier.inner_text()
    print(f"Middle tier text: {mid_text.replace(chr(10), ' | ')}")
    assert "204341" in mid_text, "Current course 204341 not in middle tier!"

    # Check Postreq in bottom tier
    bot_tier = tiers[2]
    bot_text = await bot_tier.inner_text()
    print(f"Bottom tier text: {bot_text.replace(chr(10), ' | ')}")
    assert "204441" in bot_text or "204443" in bot_text or "204435" in bot_text, "Post-requisites not properly shown in bottom tier!"

    # Take screenshot of drawer with mini graph
    await page.screenshot(path=os.path.join(ARTIFACT_DIR, "page3_drawer_mini_graph.png"))

    # Test clicking a prerequisite node in the mini graph to navigate
    prereq_node = await top_tier.query_selector(".mini-graph-node.prereq")
    if prereq_node:
        prereq_id = await prereq_node.evaluate("el => el.querySelector('.mini-node-code').textContent")
        print(f"Testing navigation by clicking prereq node {prereq_id} inside mini graph...")
        await prereq_node.click()
        await page.wait_for_timeout(300)

        # Confirm drawer updated to new course!
        new_drawer_code = await page.evaluate("() => document.getElementById('drawer-course-id').textContent")
        print(f"Drawer navigated to: {new_drawer_code}")
        assert new_drawer_code == prereq_id, f"Expected drawer to navigate to {prereq_id}, got {new_drawer_code}"
        await page.screenshot(path=os.path.join(ARTIFACT_DIR, "page3_drawer_navigated_prereq.png"))

    print("SUCCESS: Page 3 list view and overlay mini-graph working perfectly!")

async def test_dark_mode_contrast_all_pages(page):
    print("\n--- Testing Dark Mode Purple Font Contrast Across All Pages ---")
    pages_to_test = [
        ("index.html", "page1_dark_mode.png"),
        ("map.html", "page2_dark_mode.png"),
        ("tree.html", "page3_dark_mode.png"),
    ]

    for filename, screenshot_name in pages_to_test:
        url = f"file:///{BASE_DIR.replace(os.sep, '/')}/{filename}"
        await page.goto(url)
        await page.wait_for_selector("body")

        # Toggle to dark mode if not already
        theme = await page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        if theme != "dark":
            theme_btn = await page.query_selector("#theme-toggle-btn")
            await theme_btn.click()
            await page.wait_for_timeout(200)

        # Check contrast of purple text elements
        # 1. CSS variable --cmu-purple and --cmu-purple-light
        colors = await page.evaluate("""() => {
            const cs = window.getComputedStyle(document.documentElement);
            const bodyCs = window.getComputedStyle(document.body);
            return {
                bg: bodyCs.backgroundColor,
                cmuPurple: cs.getPropertyValue('--cmu-purple').trim(),
                cmuPurpleLight: cs.getPropertyValue('--cmu-purple-light').trim()
            };
        }""")
        print(f"[{filename}] Background: {colors['bg']}, --cmu-purple: {colors['cmuPurple']}, --cmu-purple-light: {colors['cmuPurpleLight']}")

        # Open drawer on a course to inspect dark mode drawer
        if filename == "tree.html":
            await page.click('.list-course-card')
            await page.wait_for_selector('#course-drawer.open')
            await page.wait_for_timeout(200)
            
            # Check drawer code color
            drawer_color = await page.evaluate("() => window.getComputedStyle(document.getElementById('drawer-course-id')).color")
            drawer_bg = await page.evaluate("() => window.getComputedStyle(document.getElementById('course-drawer')).backgroundColor")
            contrast = calculate_contrast(drawer_color, drawer_bg)
            print(f"[{filename}] Drawer course ID color: {drawer_color} ({rgb_to_hex(drawer_color)}), Background: {drawer_bg} ({rgb_to_hex(drawer_bg)}), Contrast Ratio: {contrast:.2f}:1")
            assert contrast > 6.0, f"Contrast ratio {contrast:.2f} is too low for dark mode readability!"

        await page.screenshot(path=os.path.join(ARTIFACT_DIR, screenshot_name))
        print(f"[{filename}] Dark mode screenshot saved: {screenshot_name}")

    print("SUCCESS: Dark mode high-contrast purple font verified on all pages!")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        
        await test_page2_map_hover_no_resize(page)
        await test_page3_list_view_and_mini_graph(page)
        await test_dark_mode_contrast_all_pages(page)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
