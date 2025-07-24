import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import json
import os
import re
from urllib.parse import urlparse

# Configure Gemini API
from config import GEMINI_API_KEY, NEWS_API_KEY
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Constants
MEMORY_FILE = "networking_memory.json"
MAX_CONTENT_LENGTH = 5000
REQUEST_TIMEOUT = 10

def is_valid_url(url: str) -> bool:
    """Validate if a URL is properly formatted and safe."""
    try:
        result = urlparse(url.strip())
        return all([result.scheme in ('http', 'https'), result.netloc])
    except Exception:
        return False

def sanitize_input(text: str) -> str:
    """Basic input sanitization."""
    return text.strip()[:500] if text else ""

def fetch_news(api_key: str, query: str, num_articles: int = 5) -> list:
    """Fetch news articles from NewsAPI with improved error handling."""
    if not query.strip():
        print("⚠️ No industry keyword provided for news search.")
        return []
    
    base_url = "https://newsapi.org/v2/everything"
    params = {
        "q": sanitize_input(query),
        "apiKey": api_key,
        "pageSize": num_articles,
        "language": "en",
        "sortBy": "publishedAt"
    }

    try:
        print("📰 Fetching latest industry news...")
        response = requests.get(base_url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "ok":
            print(f"⚠️ News API error: {data.get('message', 'Unknown error')}")
            return []
            
        articles = data.get("articles", [])
        if not isinstance(articles, list):
            print("⚠️ Unexpected news API response format.")
            return []
            
        print(f"✅ Found {len(articles)} recent articles")
        return articles
        
    except requests.exceptions.Timeout:
        print("⚠️ News request timed out. Continuing without news...")
        return []
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error fetching news: {e}")
        return []

def scrape_website(url: str) -> str:
    """Scrape website content with improved extraction and error handling."""
    if not is_valid_url(url):
        raise ValueError("Invalid URL provided")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print("🔍 Scraping website content...")
        response = requests.get(url, timeout=REQUEST_TIMEOUT, headers=headers)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("Website request timed out")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error fetching website: {e}")

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Extract content from multiple elements for better coverage
    content_elements = []
    
    # Get headings for structure
    headings = soup.find_all(['h1', 'h2', 'h3'])
    content_elements.extend([h.get_text().strip() for h in headings if h.get_text().strip()])
    
    # Get paragraph content
    paragraphs = soup.find_all('p')
    content_elements.extend([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
    
    # Get main content areas
    main_content = soup.find_all(['main', 'article', 'section'])
    for element in main_content:
        text = element.get_text().strip()
        if text and len(text) > 50:  # Only substantial content
            content_elements.append(text)
    
    content = " ".join(content_elements)
    
    # Clean up whitespace
    content = re.sub(r'\s+', ' ', content)
    
    print(f"✅ Extracted {len(content)} characters of content")
    return content.strip()[:MAX_CONTENT_LENGTH]

def load_memory() -> list:
    """Load networking memory from JSON file."""
    if not os.path.exists(MEMORY_FILE):
        return []
    
    try:
        with open(MEMORY_FILE, "r", encoding='utf-8') as file:
            memory = json.load(file)
            return memory if isinstance(memory, list) else []
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️ Error loading memory file: {e}")
        return []

def save_memory(memory_data: list) -> bool:
    """Save networking memory to JSON file."""
    try:
        with open(MEMORY_FILE, "w", encoding='utf-8') as file:
            json.dump(memory_data, file, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"❌ Error saving memory: {e}")
        return False

def view_past_memories():
    """Display saved networking notes from the memory file."""
    memory = load_memory()
    
    if not memory:
        print("🧠 No networking history found.")
        return

    print(f"\n📚 Past Networking Notes ({len(memory)} contacts):")
    
    for i, entry in enumerate(memory, 1):
        print(f"\n{'='*50}")
        print(f"Contact {i}")
        print(f"{'='*50}")
        print(f"👤 Name: {entry.get('name', 'N/A')}")
        print(f"💼 Role: {entry.get('role', 'N/A')}")
        print(f"🏢 Company: {entry.get('company', 'N/A')}")
        print(f"🏭 Industry: {entry.get('industry', 'N/A')}")
        print(f"🔗 LinkedIn: {entry.get('linkedin', 'N/A')}")
        print(f"🌐 Website: {entry.get('website', 'N/A')}")
        
        print(f"\n📝 AI Summary:")
        summary = entry.get('summary', 'No summary available.')
        print(f"{summary}")
        
        news_links = entry.get('news_links', [])
        if news_links:
            print(f"\n📰 Related News Links ({len(news_links)}):")
            for j, link in enumerate(news_links[:5], 1):  # Limit to 5 links
                print(f"  {j}. {link}")
        
        if i < len(memory):  # Don't prompt after last contact
            input(f"\nPress Enter to view next contact...")

def delete_contact():
    """Delete a contact from memory with improved UX."""
    memory = load_memory()
    
    if not memory:
        print("📭 No saved contacts to delete.")
        return

    print(f"\n🗑️ Select a contact to delete:\n")
    
    for i, contact in enumerate(memory, 1):
        name = contact.get('name', 'Unknown')
        company = contact.get('company', 'Unknown Company')
        role = contact.get('role', 'Unknown Role')
        print(f"  {i}. {name} - {role} at {company}")

    try:
        choice = input(f"\nEnter contact number to delete (1-{len(memory)}) or 'q' to quit: ").strip()
        
        if choice.lower() == 'q':
            print("❌ Delete cancelled.")
            return
            
        choice_num = int(choice)
        
        if 1 <= choice_num <= len(memory):
            removed = memory.pop(choice_num - 1)
            
            if save_memory(memory):
                print(f"\n✅ Successfully deleted: {removed.get('name', 'Unknown')} from {removed.get('company', 'Unknown Company')}")
                print(f"📊 {len(memory)} contacts remaining")
            else:
                print("❌ Error saving changes.")
        else:
            print(f"❌ Please enter a number between 1 and {len(memory)}.")
            
    except ValueError:
        print("❌ Please enter a valid number or 'q' to quit.")

def save_to_memory(name: str, role: str, linkedin: str, company: str, website: str, industry: str, summary: str, news_links: list = None):
    """Save a new contact to memory with validation."""
    # Validate required fields
    if not all([name.strip(), company.strip()]):
        print("❌ Name and company are required fields.")
        return False
    
    new_entry = {
        "name": sanitize_input(name),
        "role": sanitize_input(role),
        "linkedin": sanitize_input(linkedin),
        "company": sanitize_input(company),
        "website": sanitize_input(website),
        "industry": sanitize_input(industry),
        "summary": summary,
        "news_links": news_links or [],
        "created_date": __import__('datetime').datetime.now().isoformat()
    }

    memory_data = load_memory()
    memory_data.append(new_entry)

    if save_memory(memory_data):
        print(f"\n🧠 Contact saved successfully! You now have {len(memory_data)} contacts in your network.")
        return True
    else:
        print("❌ Failed to save contact.")
        return False

def get_user_input() -> dict:
    """Get and validate user input for new contact."""
    print("\n" + "="*60)
    print("📝 CONTACT INFORMATION")
    print("="*60)
    
    # Required fields
    while True:
        name = input("👤 Full name (required): ").strip()
        if name:
            break
        print("❌ Name is required. Please try again.")
    
    while True:
        company = input("🏢 Company name (required): ").strip()
        if company:
            break
        print("❌ Company name is required. Please try again.")
    
    # Optional fields
    role = input("💼 Their role/job title: ").strip()
    
    while True:
        linkedin = input("🔗 LinkedIn profile URL: ").strip()
        if not linkedin or is_valid_url(linkedin):
            break
        print("❌ Please enter a valid LinkedIn URL or leave blank.")
    
    while True:
        website = input("🌐 Company website URL: ").strip()
        if not website or is_valid_url(website):
            break
        print("❌ Please enter a valid website URL or leave blank.")
    
    industry = input("🏭 Industry keyword (for news search): ").strip()
    
    return {
        'name': name,
        'role': role,
        'linkedin': linkedin,
        'company': company,
        'website': website,
        'industry': industry
    }

def generate_summary(content: str, contact_info: dict) -> str:
    """Generate AI summary with improved prompting."""
    if not content.strip():
        return "No content available for summary."
    
    prompt = f"""
    You are a networking assistant. Analyze the following information about {contact_info['name']} from {contact_info['company']} and create a concise networking brief.

    Focus on:
    1. Key information about the person and their role
    2. Company overview and recent developments
    3. Industry trends and opportunities
    4. Potential conversation starters
    5. Ways to add value to this connection

    Content to analyze:
    {content}

    Please provide a structured summary that will help prepare for a networking conversation.
    """
    
    try:
        print("🤖 Generating AI-powered networking brief...")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"⚠️ Error generating AI summary: {e}")
        return f"Summary generation failed. Manual notes: Company website and news content were collected for {contact_info['name']} at {contact_info['company']}."

def add_new_contact():
    """Add a new contact with full research pipeline."""
    print("🚀 Let's research your networking contact!")
    
    # Get user input
    contact_info = get_user_input()
    
    # Collect content for analysis
    all_content = []
    news_links = []
    
    # Scrape website if provided
    if contact_info['website']:
        try:
            website_content = scrape_website(contact_info['website'])
            if website_content:
                all_content.append(f"Company Website Content:\n{website_content}")
        except Exception as e:
            print(f"⚠️ Website scraping failed: {e}")
    
    # Fetch news if industry provided
    if contact_info['industry']:
        try:
            news_articles = fetch_news(NEWS_API_KEY, contact_info['industry'])
            if news_articles:
                news_content = []
                for article in news_articles:
                    title = article.get('title', '')
                    description = article.get('description', '')
                    url = article.get('url', '')
                    
                    if title or description:
                        news_content.append(f"• {title}: {description}")
                        if url:
                            news_links.append(url)
                
                if news_content:
                    all_content.append(f"Recent Industry News:\n" + "\n".join(news_content))
        except Exception as e:
            print(f"⚠️ News fetching failed: {e}")
    
    # Generate summary
    combined_content = "\n\n".join(all_content) if all_content else ""
    summary = generate_summary(combined_content, contact_info)
    
    # Display results
    print("\n" + "="*60)
    print("📋 NETWORKING BRIEF")
    print("="*60)
    print(summary)
    
    if news_links:
        print(f"\n📰 Related News Articles ({len(news_links)}):")
        for i, link in enumerate(news_links[:5], 1):
            print(f"  {i}. {link}")
    
    # Save to memory
    save_to_memory(
        contact_info['name'],
        contact_info['role'], 
        contact_info['linkedin'],
        contact_info['company'],
        contact_info['website'],
        contact_info['industry'],
        summary,
        news_links
    )

def display_menu():
    """Display the main menu options."""
    print("\n" + "="*60)
    print("🔗 NETWORKING ASSISTANT")
    print("="*60)
    print("1. 👥 View past contacts")
    print("2. 🗑️  Delete a contact") 
    print("3. ➕ Add new contact")
    print("4. 🚪 Exit")
    print("="*60)

def main():
    """Main application loop with improved UX."""
    print("🌟 Welcome to your Personal Networking Assistant!")
    print("   Research contacts, save notes, and build better connections.")
    
    while True:
        display_menu()
        
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == "1":
            view_past_memories()
        elif choice == "2":
            delete_contact()
        elif choice == "3":
            add_new_contact()
        elif choice == "4":
            print("\n👋 Thanks for using Networking Assistant! Keep building those connections!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
        
        # Ask if user wants to continue
        if choice in ["1", "2", "3"]:
            continue_choice = input("\nWould you like to perform another action? (y/n): ").strip().lower()
            if continue_choice != 'y':
                print("\n👋 Thanks for using Networking Assistant! Keep building those connections!")
                break

if __name__ == "__main__":
    main()