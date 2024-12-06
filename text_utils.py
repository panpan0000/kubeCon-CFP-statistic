def clean_text(text):
    """Clean text by removing special characters and normalizing encoding"""
    if not text:
        return ""
    # Replace common problematic characters
    text = text.replace('\u2019', "'")  # Smart quotes
    text = text.replace('\u2018', "'")
    text = text.replace('\u201c', '"')  # Smart double quotes
    text = text.replace('\u201d', '"')
    text = text.replace('\u2013', '-')  # En dash
    text = text.replace('\u2014', '--')  # Em dash
    text = text.replace('\u2026', '...')  # Ellipsis
    # Remove any remaining non-ASCII characters
    text = text.encode('ascii', 'ignore').decode('ascii')
    return text.strip()
