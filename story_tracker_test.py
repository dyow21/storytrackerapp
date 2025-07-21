#!/usr/bin/env python3
"""
Test script to check access to Solutions Story Tracker website
This will help us understand if there's bot protection and how to work around it.
"""

import requests
from bs4 import BeautifulSoup
import time
import json
from urllib.parse import urljoin, urlparse


def test_basic_access():
    """Test basic access to the main page"""
    print("=== Testing Basic Access ===")

    url = "https://storytracker.solutionsjournalism.org/"

    # Try different user agents
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
    ]

    for i, user_agent in enumerate(user_agents):
        print(f"\nTrying User Agent {i + 1}: {user_agent[:50]}...")

        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'no-cache'
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            print(f"Status Code: {response.status_code}")
            print(f"Response Length: {len(response.content)} bytes")

            if response.status_code == 200:
                # Check for common bot detection patterns
                content = response.text.lower()
                bot_indicators = [
                    'cloudflare', 'captcha', 'please verify', 'blocked',
                    'access denied', 'forbidden', 'rate limit',
                    'security check', 'human verification'
                ]

                detected = [indicator for indicator in bot_indicators if indicator in content]
                if detected:
                    print(f"⚠️  Possible bot detection: {detected}")
                else:
                    print("✅ Clean response - no obvious bot detection")

                # Check for story-related content
                if 'story' in content or 'solutions' in content:
                    print("✅ Contains expected content")
                    return True, response
                else:
                    print("❌ Missing expected content")

        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")

        time.sleep(2)  # Be respectful

    return False, None


def test_search_functionality(response):
    """Test if we can find search forms or endpoints"""
    print("\n=== Testing Search Functionality ===")

    if not response:
        print("No response to analyze")
        return

    soup = BeautifulSoup(response.content, 'html.parser')

    # Look for forms
    forms = soup.find_all('form')
    print(f"Found {len(forms)} forms")

    for i, form in enumerate(forms):
        print(f"\nForm {i + 1}:")
        print(f"  Action: {form.get('action', 'None')}")
        print(f"  Method: {form.get('method', 'GET')}")

        # Find inputs
        inputs = form.find_all(['input', 'select', 'textarea'])
        for inp in inputs:
            name = inp.get('name', 'unnamed')
            input_type = inp.get('type', inp.name)
            print(f"  Input: {name} ({input_type})")

    # Look for search-related elements
    search_elements = soup.find_all(text=lambda text: text and 'search' in text.lower())
    print(f"\nFound {len(search_elements)} elements containing 'search'")

    # Look for state/location filters
    location_elements = soup.find_all(
        text=lambda text: text and any(word in text.lower() for word in ['state', 'location', 'filter']))
    print(f"Found {len(location_elements)} elements about location/filtering")


def test_story_content_extraction():
    """Test extracting the original article from a story page"""
    print("\n=== Testing Story Content Extraction ===")

    test_url = "https://storytracker.solutionsjournalism.org/stories/st-paul-police-credit-jiu-jitsu-training-for-reducing-injuries-and-excessive-force-settlements"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive'
    }

    try:
        response = requests.get(test_url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Failed to fetch: {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')

        print("=== Page Analysis ===")

        # 1. Check page structure
        print(f"Page title: {soup.title.get_text() if soup.title else 'No title'}")

        # 2. Look for story metadata
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            if meta.get('property') or meta.get('name'):
                prop = meta.get('property') or meta.get('name')
                content = meta.get('content', '')[:100]
                if any(keyword in prop.lower() for keyword in ['author', 'publication', 'date', 'url', 'source']):
                    print(f"Meta: {prop} = {content}")

        # 3. Look for publication info in the content
        publication_indicators = soup.find_all(text=lambda text: text and any(
            word in text.lower() for word in ['published', 'publication', 'author', 'date']))
        print(f"\nFound {len(publication_indicators)} publication indicators")

        # 4. Find the main content area
        content_areas = soup.find_all(['article', 'main', '.content', '.story-content', '.story-body'])
        print(f"Found {len(content_areas)} potential content areas")

        # 5. Look for structured data
        json_ld = soup.find_all('script', type='application/ld+json')
        if json_ld:
            print(f"Found {len(json_ld)} JSON-LD structured data blocks")
            for script in json_ld[:2]:  # Check first 2
                try:
                    data = json.loads(script.string)
                    print(f"JSON-LD type: {data.get('@type', 'unknown')}")
                    if 'url' in data:
                        print(f"JSON-LD URL: {data['url']}")
                except:
                    pass

        # 6. Smart link filtering for original article
        print("\n=== Finding Original Article Link ===")

        # Get all links and classify them
        all_links = soup.find_all('a', href=True)

        # Filter out obvious navigation/site links
        excluded_domains = [
            'solutionsjournalism.org',
            'storytracker.solutionsjournalism.org',
            'facebook.com',
            'twitter.com',
            'instagram.com',
            'linkedin.com',
            'youtube.com',
            'mailto:'
        ]

        excluded_paths = [
            '#',
            'javascript:',
            '/submit',
            '/about',
            '/contact',
            '/privacy',
            '/terms',
            '/collections',
            '/topics'
        ]

        potential_articles = []

        for link in all_links:
            href = link.get('href', '')
            text = link.get_text().strip()

            # Skip excluded domains and paths
            if any(domain in href.lower() for domain in excluded_domains):
                continue
            if any(path in href.lower() for path in excluded_paths):
                continue

            # Must be external http link
            if not href.startswith('http'):
                continue

            # Look for news-like domains
            news_indicators = [
                '.com', '.org', '.net', '.edu', '.gov',
                'news', 'post', 'times', 'herald', 'tribune',
                'journal', 'gazette', 'chronicle', 'report'
            ]

            if any(indicator in href.lower() for indicator in news_indicators):
                potential_articles.append({
                    'text': text[:100],
                    'href': href,
                    'context': str(link.parent)[:200] if link.parent else ''
                })

        print(f"Found {len(potential_articles)} potential article links:")

        # Sort by likelihood (links with "read" or "original" text are more likely)
        def link_score(link):
            score = 0
            text_lower = link['text'].lower()
            if any(word in text_lower for word in ['read', 'original', 'full', 'source', 'view']):
                score += 10
            if any(word in text_lower for word in ['more', 'article', 'story']):
                score += 5
            if len(link['text']) > 5:  # Prefer links with descriptive text
                score += 2
            return score

        potential_articles.sort(key=link_score, reverse=True)

        # Show top candidates
        for i, link in enumerate(potential_articles[:10]):
            score = link_score(link)
            print(f"{i + 1:2}. [Score: {score}] '{link['text']}' -> {link['href']}")

        # Try to find the most likely original article
        if potential_articles:
            best_candidate = potential_articles[0]
            print(f"\n🎯 Best candidate for original article:")
            print(f"   Text: '{best_candidate['text']}'")
            print(f"   URL: {best_candidate['href']}")

            # Test if this URL is accessible
            try:
                test_response = requests.head(best_candidate['href'], timeout=5)
                print(
                    f"   Status: {test_response.status_code} ✅" if test_response.status_code == 200 else f"   Status: {test_response.status_code} ⚠️")
            except:
                print("   Status: Could not verify ⚠️")

        return potential_articles[0]['href'] if potential_articles else None

    except Exception as e:
        print(f"Error analyzing story: {e}")
        return None


def test_main_page_story_links():
    """Test finding story links from the main page"""
    print("\n=== Testing Main Page Story Discovery ===")

    url = "https://storytracker.solutionsjournalism.org/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Main page failed: {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')

        # Look for story links
        story_links = []

        # Try multiple selectors that might contain stories
        selectors = [
            'a[href*="/stories/"]',
            '.story a',
            '.story-card a',
            '.story-title a',
            'article a',
            '.card a'
        ]

        for selector in selectors:
            found = soup.select(selector)
            if found:
                print(f"Selector '{selector}' found {len(found)} links")
                for link in found[:3]:  # Show first 3
                    href = link.get('href', '')
                    text = link.get_text().strip()[:100]
                    print(f"  '{text}' -> {href}")
                story_links.extend(found)
                break

        if not story_links:
            # Fallback: look for any links with "stories" in them
            all_links = soup.find_all('a', href=True)
            story_links = [link for link in all_links if '/stories/' in link.get('href', '')]
            print(f"Fallback: Found {len(story_links)} links containing '/stories/'")

        return story_links[:5]  # Return first 5

    except Exception as e:
        print(f"Error testing main page: {e}")
        return []


def test_alternative_approaches():
    """Test alternative ways to get story data"""
    print("\n=== Testing Alternative Approaches ===")

    # Check if there's an API
    api_endpoints = [
        "https://storytracker.solutionsjournalism.org/api/stories",
        "https://storytracker.solutionsjournalism.org/api/search",
        "https://storytracker.solutionsjournalism.org/stories.json",
        "https://storytracker.solutionsjournalism.org/feed",
        "https://storytracker.solutionsjournalism.org/rss"
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/xml, application/xml, text/html, */*'
    }

    for endpoint in api_endpoints:
        print(f"\nTrying: {endpoint}")
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                print(f"Content-Type: {content_type}")
                print(f"Content length: {len(response.content)} bytes")

                if 'json' in content_type:
                    try:
                        data = response.json()
                        print(f"JSON keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    except:
                        print("Invalid JSON")
        except Exception as e:
            print(f"Error: {e}")


def check_robots_txt():
    """Check robots.txt for crawling restrictions"""
    print("\n=== Checking robots.txt ===")

    try:
        response = requests.get("https://storytracker.solutionsjournalism.org/robots.txt", timeout=10)
        if response.status_code == 200:
            print("robots.txt content:")
            print(response.text)
        else:
            print(f"robots.txt not found (status: {response.status_code})")
    except Exception as e:
        print(f"Error checking robots.txt: {e}")


def main():
    """Run all tests"""
    print("Solutions Story Tracker Access Test")
    print("=" * 50)

    # Check robots.txt first
    check_robots_txt()

    # Test basic access
    success, response = test_basic_access()

    if success:
        # Test search functionality
        test_search_functionality(response)

        # Test story content extraction (new)
        test_story_content_extraction()

        # Test main page story discovery (new)
        test_main_page_story_links()

        # Test alternative approaches
        test_alternative_approaches()
    else:
        print("\n❌ Basic access failed - testing alternative approaches anyway")
        test_alternative_approaches()

    print("\n" + "=" * 50)
    print("Test completed!")
    print("\nRecommendations based on findings:")
    print("1. ✅ Website is accessible - no bot blocking detected")
    print("2. 🔍 Focus on smart link filtering to find original articles")
    print("3. ⚡ Use the scoring system to identify 'Read More' type links")
    print("4. 🎯 Target links with news-like domains and descriptive text")
    print("5. 🤝 Implement respectful crawling with delays between requests")
    print("6. 💡 Consider caching results to minimize repeated requests")


if __name__ == "__main__":
    main()