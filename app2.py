import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import threading
from datetime import datetime
import webbrowser
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import json
import os
import re
from urllib.parse import urlparse

# Import your existing functions (assuming config.py exists)
try:
    from config import GEMINI_API_KEY, NEWS_API_KEY
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except ImportError:
    messagebox.showerror("Configuration Error", "Please ensure config.py exists with GEMINI_API_KEY and NEWS_API_KEY")
    GEMINI_API_KEY = None
    NEWS_API_KEY = None

# Constants
MEMORY_FILE = "networking_memory.json"
MAX_CONTENT_LENGTH = 5000
REQUEST_TIMEOUT = 10

class NetworkingAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.setup_main_window()
        self.create_widgets()
        self.current_contacts = []
        self.load_contacts()
        
    def setup_main_window(self):
        """Configure the main window with modern styling."""
        self.root.title("🔗 Networking Assistant Pro")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e1e1e')
        
        # Configure modern style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Custom colors
        style.configure('Title.TLabel', 
                       background='#1e1e1e', 
                       foreground='#ffffff', 
                       font=('Segoe UI', 24, 'bold'))
        
        style.configure('Subtitle.TLabel', 
                       background='#1e1e1e', 
                       foreground='#b0b0b0', 
                       font=('Segoe UI', 12))
        
        style.configure('Modern.TButton',
                       font=('Segoe UI', 11, 'bold'),
                       padding=(20, 10))
        
        style.map('Modern.TButton',
                 background=[('active', '#0078d4'),
                           ('pressed', '#106ebe'),
                           ('!active', '#0078d4')])
        
        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.root.winfo_screenheight() // 2) - (800 // 2)
        self.root.geometry(f"1200x800+{x}+{y}")
        
    def create_widgets(self):
        """Create and layout all GUI widgets."""
        # Main container
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame, bg='#1e1e1e')
        header_frame.pack(fill='x', pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="🔗 Networking Assistant Pro", style='Title.TLabel')
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame, text="Research contacts • Save notes • Build better connections", style='Subtitle.TLabel')
        subtitle_label.pack(pady=(5, 0))
        
        # Main content area with notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Create tabs
        self.create_contacts_tab()
        self.create_add_contact_tab()
        self.create_research_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(main_frame, textvariable=self.status_var, 
                             bg='#2d2d2d', fg='#ffffff', 
                             relief='sunken', anchor='w',
                             font=('Segoe UI', 9))
        status_bar.pack(fill='x', side='bottom', pady=(10, 0))
        
    def create_contacts_tab(self):
        """Create the contacts viewing tab."""
        contacts_frame = tk.Frame(self.notebook, bg='#2d2d2d')
        self.notebook.add(contacts_frame, text="👥 My Contacts")
        
        # Toolbar
        toolbar = tk.Frame(contacts_frame, bg='#2d2d2d')
        toolbar.pack(fill='x', padx=10, pady=10)
        
        refresh_btn = ttk.Button(toolbar, text="🔄 Refresh", style='Modern.TButton',
                                command=self.load_contacts)
        refresh_btn.pack(side='left', padx=(0, 10))
        
        delete_btn = ttk.Button(toolbar, text="🗑️ Delete Selected", style='Modern.TButton',
                               command=self.delete_selected_contact)
        delete_btn.pack(side='left')
        
        # Search frame
        search_frame = tk.Frame(toolbar, bg='#2d2d2d')
        search_frame.pack(side='right')
        
        tk.Label(search_frame, text="Search:", bg='#2d2d2d', fg='#ffffff',
                font=('Segoe UI', 10)).pack(side='left', padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_contacts)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                               bg='#404040', fg='#ffffff', width=20,
                               font=('Segoe UI', 10))
        search_entry.pack(side='left')
        
        # Contacts list with treeview
        list_frame = tk.Frame(contacts_frame, bg='#2d2d2d')
        list_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Treeview for contacts
        columns = ('Name', 'Company', 'Role', 'Industry', 'Date Added')
        self.contacts_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        # Configure columns
        for col in columns:
            self.contacts_tree.heading(col, text=col)
            self.contacts_tree.column(col, width=150)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.contacts_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient='horizontal', command=self.contacts_tree.xview)
        self.contacts_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.contacts_tree.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
        
        # Bind double-click to view details
        self.contacts_tree.bind('<Double-1>', self.view_contact_details)
        
        # Contact details frame
        details_frame = tk.Frame(contacts_frame, bg='#404040')
        details_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        tk.Label(details_frame, text="Contact Details", bg='#404040', fg='#ffffff',
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=10, pady=(10, 5))
        
        self.details_text = scrolledtext.ScrolledText(details_frame, height=8, 
                                                     bg='#505050', fg='#ffffff',
                                                     font=('Segoe UI', 10),
                                                     wrap='word')
        self.details_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
    def create_add_contact_tab(self):
        """Create the add contact tab."""
        add_frame = tk.Frame(self.notebook, bg='#2d2d2d')
        self.notebook.add(add_frame, text="➕ Add Contact")
        
        # Create scrollable frame
        canvas = tk.Canvas(add_frame, bg='#2d2d2d')
        scrollbar = ttk.Scrollbar(add_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2d2d2d')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Form fields
        form_frame = tk.Frame(scrollable_frame, bg='#2d2d2d')
        form_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(form_frame, text="📝 Add New Contact", bg='#2d2d2d', fg='#ffffff',
                font=('Segoe UI', 16, 'bold')).pack(anchor='w', pady=(0, 20))
        
        # Form fields
        self.form_vars = {}
        fields = [
            ('name', '👤 Full Name *', True),
            ('company', '🏢 Company *', True),
            ('role', '💼 Job Title', False),
            ('linkedin', '🔗 LinkedIn URL', False),
            ('website', '🌐 Company Website', False),
            ('industry', '🏭 Industry Keywords', False)
        ]
        
        for field_name, label, required in fields:
            field_frame = tk.Frame(form_frame, bg='#2d2d2d')
            field_frame.pack(fill='x', pady=(0, 15))
            
            tk.Label(field_frame, text=label, bg='#2d2d2d', fg='#ffffff',
                    font=('Segoe UI', 11)).pack(anchor='w')
            
            var = tk.StringVar()
            entry = tk.Entry(field_frame, textvariable=var, bg='#404040', fg='#ffffff',
                           font=('Segoe UI', 11), width=50)
            entry.pack(anchor='w', pady=(5, 0))
            
            self.form_vars[field_name] = var
        
        # Buttons
        button_frame = tk.Frame(form_frame, bg='#2d2d2d')
        button_frame.pack(fill='x', pady=(20, 0))
        
        add_btn = ttk.Button(button_frame, text="🚀 Research & Add Contact", 
                           style='Modern.TButton', command=self.add_contact_async)
        add_btn.pack(side='left', padx=(0, 10))
        
        clear_btn = ttk.Button(button_frame, text="🗑️ Clear Form", 
                             style='Modern.TButton', command=self.clear_form)
        clear_btn.pack(side='left')
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def create_research_tab(self):
        """Create the research results tab."""
        research_frame = tk.Frame(self.notebook, bg='#2d2d2d')
        self.notebook.add(research_frame, text="🔍 Research Results")
        
        # Research display area
        self.research_text = scrolledtext.ScrolledText(research_frame, 
                                                      bg='#404040', fg='#ffffff',
                                                      font=('Segoe UI', 11),
                                                      wrap='word')
        self.research_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Initially show welcome message
        welcome_msg = """
🔍 Research Results

This tab will show detailed research results when you add a new contact.

The research includes:
• Company website analysis
• Recent industry news
• AI-generated networking brief
• Conversation starters
• Relevant news links

Add a new contact to see the research in action!
        """
        self.research_text.insert('1.0', welcome_msg)
        self.research_text.configure(state='disabled')
        
    def load_contacts(self):
        """Load contacts from memory file and populate the tree."""
        try:
            if os.path.exists(MEMORY_FILE):
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                    self.current_contacts = json.load(f)
            else:
                self.current_contacts = []
            
            self.populate_contacts_tree()
            self.status_var.set(f"Loaded {len(self.current_contacts)} contacts")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load contacts: {str(e)}")
            self.current_contacts = []
            
    def populate_contacts_tree(self, contacts=None):
        """Populate the contacts tree with data."""
        # Clear existing items
        for item in self.contacts_tree.get_children():
            self.contacts_tree.delete(item)
        
        contacts_to_show = contacts if contacts is not None else self.current_contacts
        
        for contact in contacts_to_show:
            # Format date
            date_str = contact.get('created_date', '')
            if date_str:
                try:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                except:
                    formatted_date = date_str[:10] if len(date_str) >= 10 else date_str
            else:
                formatted_date = 'Unknown'
            
            values = (
                contact.get('name', ''),
                contact.get('company', ''),
                contact.get('role', ''),
                contact.get('industry', ''),
                formatted_date
            )
            
            self.contacts_tree.insert('', 'end', values=values, tags=(contact,))
            
    def filter_contacts(self, *args):
        """Filter contacts based on search term."""
        search_term = self.search_var.get().lower()
        
        if not search_term:
            self.populate_contacts_tree()
            return
        
        filtered_contacts = []
        for contact in self.current_contacts:
            searchable_text = ' '.join([
                contact.get('name', '').lower(),
                contact.get('company', '').lower(),
                contact.get('role', '').lower(),
                contact.get('industry', '').lower()
            ])
            
            if search_term in searchable_text:
                filtered_contacts.append(contact)
        
        self.populate_contacts_tree(filtered_contacts)
        
    def view_contact_details(self, event):
        """Show detailed information for selected contact."""
        selection = self.contacts_tree.selection()
        if not selection:
            return
        
        item = self.contacts_tree.item(selection[0])
        contact_index = None
        
        # Find the contact in our list
        for i, contact in enumerate(self.current_contacts):
            if (contact.get('name') == item['values'][0] and 
                contact.get('company') == item['values'][1]):
                contact_index = i
                break
        
        if contact_index is not None:
            contact = self.current_contacts[contact_index]
            self.display_contact_details(contact)
            
    def display_contact_details(self, contact):
        """Display detailed contact information."""
        self.details_text.delete('1.0', 'end')
        
        details = f"""👤 {contact.get('name', 'N/A')}
💼 {contact.get('role', 'N/A')}
🏢 {contact.get('company', 'N/A')}
🏭 {contact.get('industry', 'N/A')}
🔗 {contact.get('linkedin', 'N/A')}
🌐 {contact.get('website', 'N/A')}

📝 AI Summary:
{contact.get('summary', 'No summary available.')}
"""
        
        news_links = contact.get('news_links', [])
        if news_links:
            details += f"\n\n📰 Related News Links ({len(news_links)}):\n"
            for i, link in enumerate(news_links[:5], 1):
                details += f"{i}. {link}\n"
        
        self.details_text.insert('1.0', details)
        
    def delete_selected_contact(self):
        """Delete the selected contact."""
        selection = self.contacts_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a contact to delete.")
            return
        
        item = self.contacts_tree.item(selection[0])
        contact_name = item['values'][0]
        company_name = item['values'][1]
        
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete {contact_name} from {company_name}?"):
            
            # Find and remove the contact
            for i, contact in enumerate(self.current_contacts):
                if (contact.get('name') == contact_name and 
                    contact.get('company') == company_name):
                    self.current_contacts.pop(i)
                    break
            
            # Save updated list
            try:
                with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.current_contacts, f, indent=2, ensure_ascii=False)
                
                self.populate_contacts_tree()
                self.details_text.delete('1.0', 'end')
                self.status_var.set(f"Deleted {contact_name}. {len(self.current_contacts)} contacts remaining.")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete contact: {str(e)}")
                
    def clear_form(self):
        """Clear all form fields."""
        for var in self.form_vars.values():
            var.set('')
        self.status_var.set("Form cleared")
        
    def add_contact_async(self):
        """Add contact in a separate thread to prevent UI freezing."""
        # Validate required fields
        name = self.form_vars['name'].get().strip()
        company = self.form_vars['company'].get().strip()
        
        if not name or not company:
            messagebox.showerror("Validation Error", "Name and Company are required fields.")
            return
        
        # Start processing in background
        self.status_var.set("🔍 Researching contact... Please wait...")
        self.notebook.select(2)  # Switch to research tab
        
        thread = threading.Thread(target=self.process_new_contact)
        thread.daemon = True
        thread.start()
        
    def process_new_contact(self):
        """Process new contact research (runs in background thread)."""
        try:
            # Get form data
            contact_info = {key: var.get().strip() for key, var in self.form_vars.items()}
            
            # Update research display
            self.root.after(0, lambda: self.update_research_display("🚀 Starting research...\n\n"))
            
            # Collect content for analysis
            all_content = []
            news_links = []
            
            # Scrape website if provided
            if contact_info['website']:
                try:
                    self.root.after(0, lambda: self.update_research_display("🌐 Analyzing company website...\n"))
                    website_content = self.scrape_website(contact_info['website'])
                    if website_content:
                        all_content.append(f"Company Website Content:\n{website_content}")
                        self.root.after(0, lambda: self.update_research_display("✅ Website analysis complete\n\n"))
                except Exception as e:
                    self.root.after(0, lambda: self.update_research_display(f"⚠️ Website scraping failed: {str(e)}\n\n"))
            
            # Fetch news if industry provided
            if contact_info['industry']:
                try:
                    self.root.after(0, lambda: self.update_research_display("📰 Fetching industry news...\n"))
                    news_articles = self.fetch_news(NEWS_API_KEY, contact_info['industry'])
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
                            self.root.after(0, lambda: self.update_research_display(f"✅ Found {len(news_articles)} news articles\n\n"))
                except Exception as e:
                    self.root.after(0, lambda: self.update_research_display(f"⚠️ News fetching failed: {str(e)}\n\n"))
            
            # Generate AI summary
            self.root.after(0, lambda: self.update_research_display("🤖 Generating AI networking brief...\n"))
            combined_content = "\n\n".join(all_content) if all_content else ""
            summary = self.generate_summary(combined_content, contact_info)
            
            # Display results
            results = f"""
📋 NETWORKING BRIEF FOR {contact_info['name'].upper()}
{'='*60}

{summary}
"""
            
            if news_links:
                results += f"\n\n📰 Related News Articles ({len(news_links)}):\n"
                for i, link in enumerate(news_links[:5], 1):
                    results += f"  {i}. {link}\n"
            
            self.root.after(0, lambda: self.show_final_results(results))
            
            # Save to memory
            self.save_contact_to_memory(contact_info, summary, news_links)
            
        except Exception as e:
            error_msg = f"❌ Error processing contact: {str(e)}"
            self.root.after(0, lambda: self.update_research_display(error_msg))
            
    def update_research_display(self, text):
        """Update the research display (called from main thread)."""
        self.research_text.configure(state='normal')
        self.research_text.insert('end', text)
        self.research_text.see('end')
        self.research_text.configure(state='disabled')
        
    def show_final_results(self, results):
        """Show final research results."""
        self.research_text.configure(state='normal')
        self.research_text.delete('1.0', 'end')
        self.research_text.insert('1.0', results)
        self.research_text.configure(state='disabled')
        
        self.status_var.set("✅ Research complete! Contact saved successfully.")
        
        # Clear form
        self.clear_form()
        
        # Reload contacts
        self.load_contacts()
        
    def save_contact_to_memory(self, contact_info, summary, news_links):
        """Save contact to memory file."""
        new_entry = {
            "name": contact_info['name'],
            "role": contact_info['role'],
            "linkedin": contact_info['linkedin'],
            "company": contact_info['company'],
            "website": contact_info['website'],
            "industry": contact_info['industry'],
            "summary": summary,
            "news_links": news_links or [],
            "created_date": datetime.now().isoformat()
        }
        
        try:
            self.current_contacts.append(new_entry)
            with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.current_contacts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Save Error", f"Failed to save contact: {str(e)}"))
    
    # Your existing utility functions (adapted for the class)
    def is_valid_url(self, url: str) -> bool:
        """Validate if a URL is properly formatted and safe."""
        try:
            result = urlparse(url.strip())
            return all([result.scheme in ('http', 'https'), result.netloc])
        except Exception:
            return False

    def scrape_website(self, url: str) -> str:
        """Scrape website content with improved extraction and error handling."""
        if not self.is_valid_url(url):
            raise ValueError("Invalid URL provided")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
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
        
        return content.strip()[:MAX_CONTENT_LENGTH]

    def fetch_news(self, api_key: str, query: str, num_articles: int = 5) -> list:
        """Fetch news articles from NewsAPI with improved error handling."""
        if not query.strip() or not api_key:
            return []
        
        base_url = "https://newsapi.org/v2/everything"
        params = {
            "q": query.strip()[:500],
            "apiKey": api_key,
            "pageSize": num_articles,
            "language": "en",
            "sortBy": "publishedAt"
        }

        try:
            response = requests.get(base_url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "ok":
                return []
                
            articles = data.get("articles", [])
            return articles if isinstance(articles, list) else []
            
        except:
            return []

    def generate_summary(self, content: str, contact_info: dict) -> str:
        """Generate AI summary with improved prompting."""
        if not content.strip() or not GEMINI_API_KEY:
            return "No content available for summary or API key missing."
        
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
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Summary generation failed: {str(e)}. Manual notes: Company website and news content were collected for {contact_info['name']} at {contact_info['company']}."

def main():
    """Main function to run the GUI application."""
    root = tk.Tk()
    app = NetworkingAssistantGUI(root)
    
    # Handle window closing
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()