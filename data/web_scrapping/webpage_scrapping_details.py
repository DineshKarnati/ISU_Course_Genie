import pandas as pd
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import os
import re


def get_chrome_driver():
    driver = None
    try:
        options = Options()
        # Uncomment the next line to run headless if you prefer:
        # options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument("--incognito")
        options.add_argument("window-size=1400,600")
        chrome_path = r"C:\Users\dines\OneDrive\Desktop\chromedriver-win64\chromedriver-win64\chromedriver.exe"  # Update path if needed
        service = Service(chrome_path)
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as exe:
        print('Exception occurred in get_chrome_driver():', exe)
    return driver


def parse_course_text(text):
    course_info = {
        'Course Code': "",
        'Course Name': "",
        'Credits': "",
        'Description': "",
        'Note': "",
        'Prerequisites': "",
        'Additional Information': "",
        'Co-requisites': "",
        'Course Fee': ""
    }

    # Normalize and split lines
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    if not lines:
        return course_info

    # Parse Course Code and Name from the first line
    code_name_line = lines[0]
    match = re.match(r'^([A-Z]{2,4} \d{3}[A-Z]?)\s*[-–]?\s*(.*)', code_name_line)
    if match:
        course_info['Course Code'] = match.group(1).strip()
        course_info['Course Name'] = match.group(2).strip()

    # Credits are on the second line (if present)
    if len(lines) > 1 and re.search(r'\d+\s*Credits?', lines[1], re.IGNORECASE):
        course_info['Credits'] = lines[1]

    # Mapping for labeled sections (e.g., Description, Prerequisites, etc.)
    label_map = {
        'description': 'Description',
        'prerequisites': 'Prerequisites',
        'note': 'Note',
        'co-requisites': 'Co-requisites',
        'corequisites': 'Co-requisites',  # just in case
        'course fee': 'Course Fee',
    }

    current_section = 'Additional Information'
    section_buffer = []

    for line in lines[2:]:
        matched = False
        for key in label_map:
            if line.lower().startswith(key):
                # Save previous section content if available
                if current_section and section_buffer:
                    course_info[current_section] = ' '.join(section_buffer).strip()
                    section_buffer = []

                current_section = label_map[key]
                content = line[len(key):].strip(': ').strip()
                if content:
                    section_buffer.append(content)
                matched = True
                break

        if not matched:
            section_buffer.append(line)

    if current_section and section_buffer:
        course_info[current_section] = ' '.join(section_buffer).strip()

    return course_info


def sanitize_filename(name):
    """
    Remove illegal characters from the filename.
    """
    return re.sub(r'[\\/*?:"<>|]', "", name)


def main():
    # Read CSV with program details. The CSV is expected to have 'Program' and 'URL' columns.
    csv_file = r'scrapped_urls.csv'  # Update with your actual CSV file path
    df_programs = pd.read_csv(csv_file, encoding='latin-1')

    # Folder to store each program's course data file
    output_folder = 'program_files'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Loop over each program in the CSV
    for idx, row in df_programs.iterrows():
        driver = get_chrome_driver()
        # if idx == 3:
        #     break
        program_name = row['Name']
        url = row['Link']
        print(f"Processing program: {program_name} at URL: {url}")
        driver.get(url)
        time.sleep(3)  # Wait for page to load; adjust if necessary

        allcourse_lst = []
        try:
            leftpad_divs = driver.find_elements(By.CSS_SELECTOR, '.custom_leftpad_20')
            if leftpad_divs:
                # Degree Map dropdowns are in the last .custom_leftpad_20 div
                degree_map_div = leftpad_divs[-1]
                degree_map_links = degree_map_div.find_elements(By.CSS_SELECTOR, 'div.acalog-core span a')
                for link in degree_map_links:
                    driver.execute_script("arguments[0].scrollIntoView();", link)
                    link.click()
                    time.sleep(1)  # Wait for the dropdown to open
                    # Extract the course description text
                    dropdown_content = driver.find_elements(By.CSS_SELECTOR, '.coursepadding > div:nth-of-type(2)')
                    for content in dropdown_content:
                        text = content.text.strip()
                        if text:
                            course_dict = parse_course_text(text)
                            if course_dict not in allcourse_lst:
                                allcourse_lst.append(course_dict)
            else:
                print("No course sections found for program:", program_name)
        except Exception as e:
            print(f"Error processing {program_name}: {e}")
        driver.quit()

        # Save the course data for the current program into its own CSV file
        if allcourse_lst:
            df_course = pd.DataFrame(allcourse_lst)
            file_name = sanitize_filename(program_name) + ".xlsx"
            file_path = os.path.join(output_folder, file_name)
            df_course.to_excel(file_path, index=False)
            print(f"Saved data for program '{program_name}' to {file_path}")
        else:
            print(f"No course data extracted for program: {program_name}")


if __name__ == "__main__":
    main()
