import asyncio
import nest_asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from services.instagram.schema import instagram_schema

nest_asyncio.apply()

async def scrape_instagram_profile():
    # Create a persistent user data directory for browser profile
    user_data_dir = ".crawl4ai/instagram_profile"
    
    browser_cfg = BrowserConfig(
        browser_type="chromium",
        headless=False,
        viewport_width=1280,
        viewport_height=720,
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116.0.0.0 Safari/537.36",
        user_data_dir=user_data_dir,
    )
    
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,  # Controls how caching is handled (ENABLED, BYPASS, DISABLED, etc.).
        log_console=True,
    )
    
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(
            url="https://www.instagram.com/cdxvy.go/",
            config=run_config,
            magic=True
        )
        
        print(f"Content length: {len(result.markdown) if result.markdown else 0}")
        print(result.metadata)
        print(result.markdown[:500] if result.markdown else "No content extracted")
        return result

if __name__ == "__main__":
    asyncio.run(scrape_instagram_profile())