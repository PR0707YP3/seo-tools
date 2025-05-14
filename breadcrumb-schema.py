import streamlit as st
import json
import pandas as pd
from io import BytesIO
from urllib.parse import urlparse
from slugify import slugify

def clean_name(segment):
    name = segment.replace("-", " ").replace("_", " ").strip()
    acronyms = ["AI", "CRM", "API", "SQL", "Node.js"]
    words = name.split()
    return " ".join([w.upper() if w.upper() in acronyms else w.capitalize() for w in words])

def generate_breadcrumb_schema_script_tag(url, base_url, separator="/"):
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.strip(separator).split(separator) if part]

    item_list = []

    # Add Home
    item_list.append({
        "@type": "ListItem",
        "position": 1,
        "name": "Home",
        "item": base_url.rstrip("/")
    })

    current_url = base_url.rstrip("/")
    for i, part in enumerate(path_parts):
        current_url += f"{separator}{part}"
        item_url = current_url + "/"
        item_list.append({
            "@type": "ListItem",
            "position": i + 2,
            "name": clean_name(part),
            "item": item_url
        })

    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": item_list
    }

    return f'''<script type="application/ld+json">
{json.dumps(schema, indent=2)}
</script>''', schema

# UI starts
st.set_page_config(page_title="Breadcrumb Schema Generator")
st.title("🔗 Bulk Breadcrumb Schema Generator")

base_url = st.text_input("Base URL (e.g. https://www.aegissofttech.com)", value="https://www.aegissofttech.com")
separator = st.text_input("Separator (default is /)", value="/")
url_input = st.text_area("Paste your URLs below (one per line):", height=200)

schemas_data = []

if st.button("Generate Breadcrumb Schema"):
    if not url_input.strip():
        st.warning("Please enter at least one URL.")
    else:
        urls = [line.strip() for line in url_input.strip().splitlines() if line.strip()]
        st.success(f"✅ Generated schemas for {len(urls)} URLs")

        for index, url in enumerate(urls, start=1):
            try:
                script_tag, _ = generate_breadcrumb_schema_script_tag(url, base_url, separator)
                filename = slugify(url.replace(base_url, "").strip("/")) or "home"
                block_id = f"schema_block_{index}"

                # Show schema
                st.markdown(f"**{index}. URL:** `{url}`")
                st.code(script_tag, language="html")

                # Copy button (JS)
                copy_button = f"""
                    <button style="margin-top: 5px;" onclick="navigator.clipboard.writeText(document.getElementById('{block_id}').innerText)">
                        📋 Copy to Clipboard
                    </button>
                    <pre id="{block_id}" style="display:none;">{script_tag}</pre>
                """
                st.markdown(copy_button, unsafe_allow_html=True)
                st.markdown("---")

                # Collect for Excel export
                schemas_data.append({
                    "URL": url,
                    "Breadcrumb Schema": script_tag
                })

            except Exception as e:
                st.error(f"Error generating schema for {url}: {e}")

# Export button if any data exists
if schemas_data:
    df = pd.DataFrame(schemas_data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Breadcrumb Schemas")
    output.seek(0)

    st.download_button(
        label="📥 Export All Schemas to Excel",
        data=output,
        file_name="breadcrumb_schemas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
