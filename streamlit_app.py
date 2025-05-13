import streamlit as st
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from datetime import datetime

# Streamlit UI setup
st.set_page_config(page_title="Auto Article Schema Generator")
st.title("📰 Auto Article Schema Generator from URLs")

base_url = st.text_input("Base URL", value="https://www.aegissofttech.com")
author_name = st.text_input("Author / Publisher Name", value="Aegis Softtech")
author_url = st.text_input("Author / Publisher URL", value=base_url)
logo_url = st.text_input("Logo URL", value="https://www.aegissofttech.com/insights/wp-content/uploads/2024/07/logo.webp")

st.markdown("### 📥 Enter Article URLs (One per line)")
url_input = st.text_area("Example:\nhttps://www.example.com/article-1\nhttps://www.example.com/article-2", height=200)

schemas_data = []

def extract_article_metadata(url):
    res = requests.get(url, timeout=10)
    soup = BeautifulSoup(res.content, 'html.parser')

    # Title: prefer og:title > <title>
    title = soup.find("meta", property="og:title")
    title = title["content"].strip() if title and title.get("content") else soup.title.string.strip()

    # Image
    image = soup.find("meta", property="og:image")
    image_url = image["content"].strip() if image and image.get("content") else ""

    return title, image_url

def generate_article_schema(url, headline, image_url):
    # Use current timestamp for both datePublished and dateModified
    now_iso = datetime.now().isoformat(timespec='seconds') + "+05:30"

    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": url
        },
        "headline": headline,
        "image": image_url,
        "author": {
            "@type": "Organization",
            "name": author_name,
            "url": author_url
        },
        "publisher": {
            "@type": "Organization",
            "name": author_name,
            "logo": {
                "@type": "ImageObject",
                "url": logo_url
            }
        },
        "datePublished": now_iso,
        "dateModified": now_iso
    }

    return f'''<script type="application/ld+json">
{json.dumps(schema, indent=2)}
</script>''', schema

# On Submit
if st.button("Generate Article Schemas"):
    if not url_input.strip():
        st.warning("Please enter at least one URL.")
    else:
        urls = [u.strip() for u in url_input.strip().splitlines() if u.strip()]
        st.success(f"✅ Generating schemas for {len(urls)} URLs...")

        for index, url in enumerate(urls, start=1):
            try:
                title, image = extract_article_metadata(url)
                schema_tag, _ = generate_article_schema(url, title, image)

                st.markdown(f"**{index}. URL:** `{url}`")
                st.code(schema_tag, language="html")

                block_id = f"schema_block_{index}"
                st.markdown(f"""
                    <button onclick="navigator.clipboard.writeText(document.getElementById('{block_id}').innerText)">📋 Copy to Clipboard</button>
                    <pre id="{block_id}" style="display:none;">{schema_tag}</pre>
                """, unsafe_allow_html=True)

                schemas_data.append({
                    "URL": url,
                    "Title": title,
                    "Image": image,
                    "Generated Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Article Schema": schema_tag
                })

                st.markdown("---")

            except Exception as e:
                st.error(f"❌ Error for {url}: {e}")

# Excel export
if schemas_data:
    df = pd.DataFrame(schemas_data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Article Schemas")
    output.seek(0)

    st.download_button(
        label="📥 Export All Schemas to Excel",
        data=output,
        file_name="article_schemas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
