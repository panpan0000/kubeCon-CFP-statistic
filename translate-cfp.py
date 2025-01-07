import pandas as pd
import asyncio
from deep_translator import GoogleTranslator

# Load the uploaded CSV file to check its structure and content
#file_path = 'kubeCon-CFP-2024EU-AI-Track.csv'
#data = pd.read_csv(file_path)

# Columns to translate
columns_to_translate = ['title', 'description', 'ecosystem_benefits', 'additional_resources']

# Async function to translate text
async def translate_text(text, src='en', dest='zh-CN'):
    try:
        # Use GoogleTranslator from deep_translator which supports async
        if isinstance(text, str):
            return GoogleTranslator(source=src, target=dest).translate(text)
        return text
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return the original text if translation fails

# Async function to translate the dataframe
async def translate_dataframe(df):
    # Create a copy of the dataframe to avoid SettingWithCopyWarning
    df_translated = df.copy()
    
    # Use asyncio.gather to translate columns concurrently
    for column in columns_to_translate:
        # Create translation tasks for each text in the column
        translation_tasks = [translate_text(text) for text in df[column]]
        
        # Wait for all translations to complete
        translated_texts = await asyncio.gather(*translation_tasks)
        
        # Assign translated texts to new columns
        df_translated[f'{column}_cn'] = translated_texts
    
    return df_translated

# Run the async translation
async def main():
    data = pd.read_csv(file_path)

    # Translate the selected columns
    data_translated = await translate_dataframe(data)

    # Save the translated data to a new CSV file
    translated_file_path = output_file
    data_translated.to_csv(translated_file_path, index=False, encoding='utf-8')
    print(f"Translation completed. File saved to {translated_file_path}")

# Run the async main function
if __name__ == '__main__':
   # Set up argument parser
    parser = argparse.ArgumentParser(description='Translate CSV columns from English to Chinese')
    parser.add_argument('file_path', help='Path for the input CSV file')
    parser.add_argument('output_file', nargs='?', 
                        default='kubeCon-CFP-2024EU-AI-Track-Translated.csv', 
                        help='Path to the output CSV file (optional, default: kubeCon-CFP-2024EU-AI-Track-Translated.csv)')
    
    # Parse arguments
    args = parser.parse_args()
    
    asyncio.run(main())
