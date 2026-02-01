import time
import cloudscraper
from os.path import join, expanduser
from os import makedirs
from bs4 import BeautifulSoup
from typing import Optional
headers = {'Accept-Encoding': 'identity', 'User-Agent': 'Defined'}
scraper = cloudscraper.create_scraper()

MAX_RETRIES = 3
RETRY_DELAY = 2



def download_book(book_url: str, book_title: str = "Unknown Book", custom_destination: Optional[str] = None):
    if custom_destination:
        destination = custom_destination
    else:
        destination = join(expanduser("~"), "Downloads")
    
    makedirs(destination, exist_ok=True)
    print(f"Fetching book page: {book_url}")
    
    response = _fetch_with_retry(book_url, "book page")
    
    html = BeautifulSoup(response.text, "html.parser")
    forms = html.find_all('form', {'action': lambda x: x and 'Fetching_Resource.php' in x})
    
    if not forms:
        print("No download forms found")
        raise ValueError("Could not find download form on page")
    
    selected_form = _select_download_form(forms)
    
    if not selected_form:
        print("No valid download form found")
        raise ValueError("Could not find epub or pdf download form")
    
    form_action, server_id, filename = _extract_form_data(selected_form)
    
    print(f"Form action: {form_action}")
    print(f"Server ID: {server_id}")
    print(f"Filename: {filename}")
    
    form_data = {'id': server_id, 'filename': filename}
    print(f"Submitting form to download file...")
    
    download_response = _submit_form_with_retry(form_action, form_data)
    
    actual_download_url = _parse_redirect_url(download_response.text)
    
    print(f"Downloading file from: {actual_download_url}")
    
    file_response = _fetch_with_retry(actual_download_url, "file")
    
    filepath = join(destination, filename)
    with open(filepath, 'wb') as file:
        file.write(file_response.content)
    
    print(f"Successfully downloaded to: {filepath}")
    
    return {"filename": filename, "destination": destination, "filepath": filepath}


def _fetch_with_retry(url: str, description: str = "resource"):
    for attempt in range(MAX_RETRIES):
        try:
            response = scraper.get(url, headers=headers)
            return response
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_DELAY * (attempt + 1)
                print(f"Connection error fetching {description} (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Failed to fetch {description} after {MAX_RETRIES} attempts")
                raise


def _submit_form_with_retry(form_action: str, form_data: dict):
    for attempt in range(MAX_RETRIES):
        try:
            response = scraper.post(form_action, data=form_data, headers=headers, allow_redirects=True)
            return response
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_DELAY * (attempt + 1)
                print(f"Connection error submitting form (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Failed to submit form after {MAX_RETRIES} attempts")
                raise


def _select_download_form(forms):
    for form in forms:
        filename_input = form.find('input', {'name': 'filename'})
        if filename_input:
            filename_value = filename_input.get('value', '')
            if filename_value.endswith('.epub'):
                print(f"Found EPUB form: {filename_value}")
                return form
    
    for form in forms:
        filename_input = form.find('input', {'name': 'filename'})
        if filename_input:
            filename_value = filename_input.get('value', '')
            if filename_value.endswith('.pdf'):
                print(f"Found PDF form (no EPUB available): {filename_value}")
                return form
    
    return None


def _extract_form_data(form):
    form_action = form.get('action')
    form_id = form.find('input', {'name': 'id'})
    form_filename = form.find('input', {'name': 'filename'})
    
    if not form_action or not form_id or not form_filename:
        print("Form missing required fields")
        raise ValueError("Download form is incomplete")
    
    server_id = form_id.get('value')
    filename = form_filename.get('value')
    
    return form_action, server_id, filename


def _parse_redirect_url(html_content: str) -> str:
    redirect_html = BeautifulSoup(html_content, "html.parser")
    meta_refresh = redirect_html.find('meta', attrs={'http-equiv': 'Refresh'})
    
    if not meta_refresh:
        print("Could not find redirect URL")
        raise ValueError("Could not find download redirect")
    
    content_attr = meta_refresh.get('content', '')
    if 'url=' in content_attr:
        actual_download_url = content_attr.split('url=')[1]
        print(f"Found actual download URL: {actual_download_url}")
        return actual_download_url
    else:
        print("Could not parse redirect URL")
        raise ValueError("Could not parse download URL")
